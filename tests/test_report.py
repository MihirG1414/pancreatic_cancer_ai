"""Synthetic software checks for annotation-derived report calculations."""

import matplotlib

matplotlib.use("Agg")

import nibabel as nib
import numpy as np
import pytest

from mirai_ct.volume import load_volume


def paired_images(tmp_path, labels, affine=None, units="mm"):
    affine = np.diag([2.0, 3.0, 4.0, 1.0]) if affine is None else affine
    for name, data in [("scan", np.zeros(labels.shape, dtype=np.int16)), ("mask", labels)]:
        image = nib.Nifti1Image(data, affine)
        image.header.set_xyzt_units(units)
        nib.save(image, tmp_path / f"{name}.nii.gz")
    return load_volume(tmp_path / "scan.nii.gz"), load_volume(tmp_path / "mask.nii.gz")


def test_annotation_counts_bounds_and_oblique_voxel_volume(tmp_path):
    from mirai_ct.report import annotation_measurements

    labels = np.zeros((5, 6, 4), dtype=np.uint8)
    labels[1:3, 2:5, 1:3] = 1
    labels[4, 0, 3] = 2
    affine = np.array([[2, 1, 0, 0], [0, 3, 0, 0], [0, 0, 4, 0], [0, 0, 0, 1]])
    scan, mask = paired_images(tmp_path, labels, affine)
    rows = {row["label_id"]: row for row in annotation_measurements(scan, mask)}
    assert rows[0]["voxel_count"] == 107
    assert rows[1]["voxel_count"] == 12
    assert rows[1]["bbox_min_ijk"] == [1, 2, 1]
    assert rows[1]["bbox_max_ijk"] == [2, 4, 2]
    assert rows[1]["volume_mm3"] == pytest.approx(288)
    assert rows[1]["volume_ml"] == pytest.approx(0.288)
    assert rows[2]["bbox_min_ijk"] == [4, 0, 3]
    assert rows[2]["bbox_max_ijk"] == [4, 0, 3]
    assert not scan.in_memory and not mask.in_memory


def test_unknown_units_refuse_unsafe_overlay_and_measurement(tmp_path):
    from mirai_ct.report import annotation_measurements

    labels = np.zeros((3, 3, 2), dtype=np.uint8)
    labels[1, 1, 1] = 2
    scan, mask = paired_images(tmp_path, labels, units="unknown")
    with pytest.raises(ValueError, match="Spatial units are unknown"):
        annotation_measurements(scan, mask)


@pytest.mark.parametrize("value", [-1, 0.5, 65536])
def test_invalid_label_values_fail(tmp_path, value):
    from mirai_ct.report import annotation_measurements

    labels = np.zeros((3, 3, 2), dtype=np.float32)
    labels[1, 1, 1] = value
    scan, mask = paired_images(tmp_path, labels)
    with pytest.raises(ValueError, match="nonnegative integer"):
        annotation_measurements(scan, mask)


def test_geometry_mismatch_fails_before_measuring(tmp_path):
    from mirai_ct.report import annotation_measurements

    scan, mask = paired_images(tmp_path, np.ones((3, 3, 2), dtype=np.uint8))
    mask.affine[0, 3] += 8
    with pytest.raises(ValueError, match="geometry"):
        annotation_measurements(scan, mask)


def test_report_cli_creates_local_html_and_native_views(tmp_path, monkeypatch):
    from mirai_ct.report import main

    labels = np.zeros((12, 14, 8), dtype=np.uint8)
    labels[3:8, 4:9, 4] = 2
    paired_images(tmp_path, labels)
    manifest = tmp_path / "cases.csv"
    manifest.write_text(
        "case_id,scan_path,label_path,dataset_source\n"
        "synthetic,scan.nii.gz,mask.nii.gz,MSD Task07 Pancreas synthetic\n"
    )
    output = tmp_path / "report"
    monkeypatch.setattr(
        "sys.argv",
        [
            "mirai_ct.report",
            "--manifest",
            str(manifest),
            "--case-id",
            "synthetic",
            "--output",
            str(output),
        ],
    )
    assert main() == 0
    html = (output / "index.html").read_text(encoding="utf-8")
    assert "Dataset annotation" in html
    assert "Cancer" in html
    assert "[3, 4, 4]" in html
    assert "[7, 8, 4]" in html
    assert "not a model prediction" in html
    assert all((output / f"axis-{axis}.png").is_file() for axis in range(3))
    assert main() == 1  # existing directory must not be overwritten


def test_report_cli_rejects_unknown_case_before_output(tmp_path, monkeypatch):
    from mirai_ct.report import main

    manifest = tmp_path / "cases.csv"
    manifest.write_text("case_id,scan_path,label_path,dataset_source\n")
    output = tmp_path / "report"
    monkeypatch.setattr(
        "sys.argv",
        [
            "mirai_ct.report",
            "--manifest",
            str(manifest),
            "--case-id",
            "missing",
            "--output",
            str(output),
        ],
    )
    assert main() == 1
    assert not output.exists()
