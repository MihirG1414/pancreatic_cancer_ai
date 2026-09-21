"""Download one real MSD CT/mask pair, never the full archive (stdlib only).

The fixed offsets were checked against the official MSD EU mirror on 2026-09-21 UTC.
An archive change fails closed: do not change the ETag without rechecking the tar.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import sys
import tarfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO
from urllib.error import URLError
from urllib.request import Request, urlopen

ARCHIVE_URL = "https://msd-for-monai-eu.s3.eu-west-2.amazonaws.com/Task07_Pancreas.tar"
ARCHIVE_SIZE = 12_289_971_712
ARCHIVE_ETAG = '"324a716d282dfd690c910d14dc153efd-733"'
CHUNK_SIZE = 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 1024 * 1024 * 1024


@dataclass(frozen=True)
class Member:
    name: str
    header_offset: int
    size: int

    @property
    def payload_offset(self) -> int:
        return self.header_offset + 512


DATASET = Member("Task07_Pancreas/dataset.json", 19_456, 28_581)
SCAN = Member("Task07_Pancreas/imagesTr/pancreas_290.nii.gz", 4_127_080_960, 28_093_127)
LABEL = Member("Task07_Pancreas/labelsTr/pancreas_290.nii.gz", 12_281_422_336, 28_963)


def read_range(start: int, size: int, sink: BinaryIO) -> str:
    """Validate response headers before reading, stream exact bytes, return SHA256."""
    end = start + size - 1
    if start < 0 or size <= 0 or end >= ARCHIVE_SIZE:
        raise ValueError("Invalid archive byte range")
    request = Request(
        ARCHIVE_URL,
        headers={
            "Range": f"bytes={start}-{end}",
            "If-Match": ARCHIVE_ETAG,
            "Accept-Encoding": "identity",
            "User-Agent": "Mirai-CT-milestone-1/0.1",
        },
    )
    digest = hashlib.sha256()
    with urlopen(request, timeout=60) as response:
        if response.status != 206:
            raise ValueError("Server did not return HTTP 206; refusing whole archive download")
        expected_range = f"bytes {start}-{end}/{ARCHIVE_SIZE}"
        if response.headers.get("Content-Range") != expected_range:
            raise ValueError("Server returned an unexpected Content-Range")
        if response.headers.get("ETag") != ARCHIVE_ETAG:
            raise ValueError("Archive ETag changed; offsets must be verified again")
        if response.headers.get("Content-Length") != str(size):
            raise ValueError("Server returned an unexpected Content-Length")
        if response.headers.get("Content-Encoding", "identity") != "identity":
            raise ValueError("HTTP content encoding would change archive byte offsets")
        remaining = size
        while remaining:
            chunk = response.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                raise ValueError("Payload length is shorter than the requested byte range")
            sink.write(chunk)
            digest.update(chunk)
            remaining -= len(chunk)
        if response.read(1):
            raise ValueError("Payload length exceeds the requested byte range")
    return digest.hexdigest()


def verify_header(raw: bytes, member: Member) -> None:
    """tarfile verifies the tar header checksum; no archive extraction is used."""
    try:
        header = tarfile.TarInfo.frombuf(raw, "utf-8", "strict")
    except (tarfile.HeaderError, UnicodeError) as exc:
        raise ValueError("Invalid tar header or checksum") from exc
    if header.name != member.name or header.size != member.size or not header.isfile():
        raise ValueError("Tar member name, size, or regular-file type does not match")


def download_member(member: Member, destination: Path) -> dict:
    """Preserve compressed bytes and verify gzip CRC without caching the full volume."""
    output = destination / member.name
    partial = output.with_name(output.name + ".part")
    if output.exists() or partial.exists():
        raise FileExistsError(f"Refusing to overwrite existing file: {output} (or .part)")
    header = io.BytesIO()
    read_range(member.header_offset, 512, header)
    verify_header(header.getvalue(), member)
    output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation means another process's partial file is never removed.
    with partial.open("xb") as sink:
        try:
            digest = read_range(member.payload_offset, member.size, sink)
        except BaseException:
            sink.close()
            partial.unlink(missing_ok=True)
            raise
    uncompressed_bytes = None
    try:
        if member.name.endswith(".nii.gz"):
            uncompressed_bytes = 0
            with gzip.open(partial, "rb") as source:
                while block := source.read(CHUNK_SIZE):
                    uncompressed_bytes += len(block)
                    if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                        raise ValueError("Sample exceeds the 1 GiB uncompressed safety limit")
        # On native Windows rename refuses an existing target, including a concurrent writer.
        partial.rename(output)
    except BaseException:
        partial.unlink(missing_ok=True)
        raise
    return {
        "archive_member": member.name,
        "path": str(output.resolve()),
        "payload_start": member.payload_offset,
        "payload_end": member.payload_offset + member.size - 1,
        "compressed_bytes": member.size,
        "sha256": digest,
        "gzip_crc_checked": member.name.endswith(".nii.gz"),
        "uncompressed_bytes": uncompressed_bytes,
    }


def download_sample(destination: Path) -> Path:
    """Fetch dataset provenance first, then exactly one CT and its existing annotation."""
    destination = destination.resolve()
    provenance_path = destination / "sample_provenance.json"
    for output in [provenance_path, *(destination / m.name for m in (DATASET, SCAN, LABEL))]:
        if output.exists() or output.with_name(output.name + ".part").exists():
            raise FileExistsError(f"Destination already contains sample output: {output}")
    print("Downloading one REAL MSD CT and existing label (~28.2 MB); no predictions.")
    metadata_record = download_member(DATASET, destination)
    metadata = json.loads((destination / DATASET.name).read_text(encoding="utf-8"))
    expected_pair = {
        "image": "./imagesTr/pancreas_290.nii.gz",
        "label": "./labelsTr/pancreas_290.nii.gz",
    }
    if expected_pair not in metadata.get("training", []):
        raise ValueError("dataset.json does not identify the expected scan/label pair")
    if metadata.get("licence") != "CC-BY-SA 4.0":
        raise ValueError("Unexpected dataset license; inspect the official source")
    records = [metadata_record]
    for member in (SCAN, LABEL):
        print(f"Fetching {member.name}: {member.size:,} bytes", flush=True)
        records.append(download_member(member, destination))
    provenance = {
        "case_id": "pancreas_290",
        "data_kind": "real public CT and existing segmentation; not model predictions",
        "retrieved_utc": datetime.now(UTC).isoformat(),
        "dataset_source": "Medical Segmentation Decathlon Task07 Pancreas",
        "provider": metadata.get("reference"),
        "registry_url": "https://registry.opendata.aws/msd/",
        "license": metadata["licence"],
        "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
        "archive_url": ARCHIVE_URL,
        "archive_size": ARCHIVE_SIZE,
        "archive_etag": ARCHIVE_ETAG,
        "labels": metadata.get("labels"),
        "integrity_note": (
            "SHA256 recorded locally for reproducibility; no publisher per-case hash available. "
            "Tar header checksums, pinned archive ETag, exact ranges, lengths and gzip CRC checked."
        ),
        "files": records,
    }
    with provenance_path.open("x", encoding="utf-8") as sink:
        json.dump(provenance, sink, indent=2)
        sink.write("\n")
    print(f"Saved real scan, existing label, dataset.json and provenance: {destination}")
    return provenance_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path, default=Path("D:/MiraiData/MSD_Task07"))
    args = parser.parse_args()
    try:
        download_sample(args.destination)
    except (OSError, ValueError, EOFError, URLError) as exc:
        print(f"Download stopped: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
