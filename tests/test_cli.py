import json
import subprocess
import sys

import nibabel as nib
import numpy as np


def test_cli_metadata_and_saved_slice(tmp_path):
    path = tmp_path / "synthetic.nii.gz"
    nib.save(nib.Nifti1Image(np.zeros((10, 11, 12), dtype=np.int16), np.eye(4)), path)
    output = tmp_path / "synthetic.png"
    result = subprocess.run(
        [sys.executable, "-m", "mirai_ct", str(path), "--output", str(output)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert output.read_bytes().startswith(b"\x89PNG")
    report, _ = json.JSONDecoder().raw_decode(result.stdout)
    assert report["scan"]["shape"] == [10, 11, 12]
    assert report["scan"]["full_volume_cached"] is False


def test_cli_missing_scan_is_explicit(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "mirai_ct", str(tmp_path / "missing.nii.gz")],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 1
    assert "file not found" in result.stderr
    assert "Traceback" not in result.stderr
