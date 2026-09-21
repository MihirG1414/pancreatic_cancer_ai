"""Synthetic HTTP/tar fixtures only: these tests do not download medical data."""

import gzip
import hashlib
import importlib.util
import io
import json
import sys
import tarfile
from pathlib import Path

import pytest


@pytest.fixture
def downloader():
    path = Path(__file__).resolve().parents[1] / "scripts" / "download_sample.py"
    assert path.exists(), "The bounded downloader has not been implemented"
    spec = importlib.util.spec_from_file_location("download_sample", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class Response(io.BytesIO):
    def __init__(self, body, *, status=206, headers=None):
        super().__init__(body)
        self.status = status
        self.headers = headers or {}
        self.read_calls = 0

    def read(self, size=-1):
        self.read_calls += 1
        assert 0 <= size <= 1024 * 1024, "Every body read must be bounded"
        return super().read(size)


def response_for(module, start, size, body, **overrides):
    headers = {
        "Content-Range": f"bytes {start}-{start + size - 1}/{module.ARCHIVE_SIZE}",
        "Content-Length": str(size),
        "ETag": module.ARCHIVE_ETAG,
    }
    headers.update(overrides)
    return Response(body, headers=headers)


@pytest.mark.parametrize("change", ["status", "range", "etag", "length", "encoding"])
def test_rejects_unsafe_response_without_reading_body(downloader, monkeypatch, change):
    response = response_for(downloader, 12, 4, b"data")
    if change == "status":
        response.status = 200
    elif change == "range":
        response.headers["Content-Range"] = "bytes 0-3/9999"
    elif change == "etag":
        response.headers["ETag"] = '"changed-archive"'
    elif change == "length":
        response.headers["Content-Length"] = "12289971712"
    else:
        response.headers["Content-Encoding"] = "gzip"
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: response)
    with pytest.raises(ValueError):
        downloader.read_range(12, 4, io.BytesIO())
    assert response.read_calls == 0


@pytest.mark.parametrize("body", [b"abc", b"abcde"])
def test_rejects_short_or_oversized_payload(downloader, monkeypatch, body):
    response = response_for(downloader, 12, 4, body)
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: response)
    with pytest.raises(ValueError, match="length"):
        downloader.read_range(12, 4, io.BytesIO())


def test_sends_exact_range_and_identity_and_streams(downloader, monkeypatch):
    body = b"x" * (1024 * 1024 + 12)
    response = response_for(downloader, 12, len(body), body)

    def open_response(request, timeout):
        assert request.full_url == downloader.ARCHIVE_URL
        assert request.get_header("Range") == f"bytes=12-{11 + len(body)}"
        assert request.get_header("If-match") == downloader.ARCHIVE_ETAG
        assert request.get_header("Accept-encoding") == "identity"
        assert timeout > 0
        return response

    monkeypatch.setattr(downloader, "urlopen", open_response)
    sink = io.BytesIO()
    digest = downloader.read_range(12, len(body), sink)
    assert sink.getvalue() == body
    assert digest == hashlib.sha256(body).hexdigest()
    assert response.read_calls >= 2


@pytest.mark.parametrize("defect", ["name", "size", "type", "checksum"])
def test_rejects_wrong_tar_member(downloader, defect):
    member = downloader.Member("imagesTr/sample.nii.gz", 512, 12)
    header = tarfile.TarInfo(member.name)
    header.size = member.size
    if defect == "name":
        header.name = "other.nii.gz"
    elif defect == "size":
        header.size += 1
    elif defect == "type":
        header.type = tarfile.SYMTYPE
    raw = header.tobuf()
    if defect == "checksum":
        raw = b"Z" + raw[1:]
    with pytest.raises(ValueError):
        downloader.verify_header(raw, member)


def test_member_download_verifies_gzip_and_writes_no_overwrite(downloader, monkeypatch, tmp_path):
    body = gzip.compress(b"synthetic software check", mtime=0)
    member = downloader.Member("imagesTr/sample.nii.gz", 512, len(body))
    header = tarfile.TarInfo(member.name)
    header.size = len(body)
    responses = iter(
        [
            response_for(downloader, 512, 512, header.tobuf()),
            response_for(downloader, 1024, len(body), body),
        ]
    )
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: next(responses))
    result = downloader.download_member(member, tmp_path)
    output = tmp_path / member.name
    assert output.read_bytes() == body
    assert result["sha256"] == hashlib.sha256(body).hexdigest()
    assert result["uncompressed_bytes"] == len(b"synthetic software check")
    assert not output.with_name(output.name + ".part").exists()
    with pytest.raises(FileExistsError):
        downloader.download_member(member, tmp_path)


def test_invalid_gzip_removes_partial_file(downloader, monkeypatch, tmp_path):
    body = b"not a gzip file"
    member = downloader.Member("imagesTr/sample.nii.gz", 512, len(body))
    header = tarfile.TarInfo(member.name)
    header.size = len(body)
    responses = iter(
        [
            response_for(downloader, 512, 512, header.tobuf()),
            response_for(downloader, 1024, len(body), body),
        ]
    )
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: next(responses))
    with pytest.raises((OSError, EOFError, ValueError)):
        downloader.download_member(member, tmp_path)
    assert not list(tmp_path.rglob("*.part"))
    assert not (tmp_path / member.name).exists()


def test_truncated_member_cleans_partial_and_preserves_existing_partial(
    downloader, monkeypatch, tmp_path
):
    member = downloader.Member("imagesTr/sample.nii.gz", 512, 100)
    header = tarfile.TarInfo(member.name)
    header.size = member.size
    responses = iter(
        [
            response_for(downloader, 512, 512, header.tobuf()),
            response_for(downloader, 1024, 100, b"truncated"),
        ]
    )
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: next(responses))
    with pytest.raises(ValueError, match="length"):
        downloader.download_member(member, tmp_path)
    partial = (tmp_path / member.name).with_suffix(".gz.part")
    assert not partial.exists()
    partial.write_bytes(b"existing work")
    with pytest.raises(FileExistsError):
        downloader.download_member(member, tmp_path)
    assert partial.read_bytes() == b"existing work"


@pytest.mark.parametrize("matching_pair", [True, False])
def test_sample_orchestration_and_provenance(downloader, monkeypatch, tmp_path, matching_pair):
    pair = {
        "image": "./imagesTr/pancreas_290.nii.gz",
        "label": "./labelsTr/pancreas_290.nii.gz",
    }
    metadata = json.dumps(
        {
            "training": [pair] if matching_pair else [],
            "licence": "CC-BY-SA 4.0",
            "reference": "Synthetic test metadata only",
            "labels": {"0": "background"},
        }
    ).encode()
    bodies = [metadata, gzip.compress(b"synthetic scan"), gzip.compress(b"synthetic label")]
    responses = []
    for index, (name, body) in enumerate(zip(["DATASET", "SCAN", "LABEL"], bodies, strict=True)):
        original = getattr(downloader, name)
        member = downloader.Member(original.name, index * 4096, len(body))
        monkeypatch.setattr(downloader, name, member)
        header = tarfile.TarInfo(member.name)
        header.size = member.size
        responses.extend(
            [
                response_for(downloader, member.header_offset, 512, header.tobuf()),
                response_for(downloader, member.payload_offset, member.size, body),
            ]
        )
    pending = iter(responses)
    monkeypatch.setattr(downloader, "urlopen", lambda *a, **kw: next(pending))
    if not matching_pair:
        with pytest.raises(ValueError, match="scan/label pair"):
            downloader.download_sample(tmp_path)
        assert not (tmp_path / downloader.SCAN.name).exists()
        assert not (tmp_path / "sample_provenance.json").exists()
        assert responses[2].read_calls == 0
        return
    provenance = json.loads(downloader.download_sample(tmp_path).read_text())
    assert provenance["archive_etag"] == downloader.ARCHIVE_ETAG
    assert provenance["license"] == "CC-BY-SA 4.0"
    assert provenance["retrieved_utc"].endswith("+00:00")
    assert len(provenance["files"]) == 3
    assert provenance["files"][1]["sha256"] == hashlib.sha256(bodies[1]).hexdigest()
    assert (tmp_path / downloader.LABEL.name).read_bytes() == bodies[2]
    with pytest.raises(FileExistsError):
        downloader.download_sample(tmp_path)
