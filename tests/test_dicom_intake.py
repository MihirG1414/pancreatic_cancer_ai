"""Synthetic conventional CT stacks; no fabricated clinical scan or prediction."""

from copy import deepcopy

import numpy as np
import pytest


def stack():
    return [
        {
            "modality": "CT",
            "sop_uid": f"slice-{k}",
            "frames": 1,
            "position": [-20.0, 30.0, 10.0 + k * 2.5],
            "orientation": [1, 0, 0, 0, 1, 0],
            "pixel_spacing": [0.8, 0.6],
            "rows": 4,
            "columns": 5,
            "slope": 1.0,
            "intercept": -1024.0,
            "rescale_type": "HU",
        }
        for k in range(3)
    ]


def test_native_stack_geometry_uses_positions_not_slice_thickness():
    from mirai_ct.dicom_intake import validate_stack

    result = validate_stack(stack())
    assert result["size"] == [5, 4, 3]
    assert result["spacing"] == [0.6, 0.8, 2.5]
    assert result["origin_lps"] == [-20, 30, 10]
    assert result["direction_lps"] == np.eye(3).ravel().tolist()
    assert result["hu_calibration"] == "DICOM rescale type HU; physical calibration unverified"


@pytest.mark.parametrize(
    "failure", ["gap", "tilt", "duplicate", "orientation", "spacing", "frames", "modality", "nan"]
)
def test_unsafe_dicom_stacks_are_rejected(failure):
    from mirai_ct.dicom_intake import validate_stack

    records = deepcopy(stack())
    if failure == "gap":
        records[2]["position"][2] += 1
    elif failure == "tilt":
        records[1]["position"][0] += 0.1
    elif failure == "duplicate":
        records[1]["sop_uid"] = records[0]["sop_uid"]
    elif failure == "orientation":
        records[1]["orientation"] = [0, 1, 0, 1, 0, 0]
    elif failure == "spacing":
        records[1]["pixel_spacing"][0] *= 2
    elif failure == "frames":
        records[1]["frames"] = 2
    elif failure == "modality":
        records[1]["modality"] = "MR"
    else:
        records[1]["position"][2] = np.nan
    with pytest.raises(ValueError):
        validate_stack(records)


def test_reflected_oblique_stack_preserves_native_direction():
    from mirai_ct.dicom_intake import validate_stack

    records = stack()
    orientation = [0, 1, 0, 1, 0, 0]
    for k, row in enumerate(records):
        row["orientation"] = orientation
        row["position"] = [-20, 30, 10 - 2.5 * k]
    got = validate_stack(records)
    direction = np.asarray(got["direction_lps"]).reshape(3, 3)
    np.testing.assert_array_equal(direction, [[0, 1, 0], [1, 0, 0], [0, 0, -1]])


def test_convert_conventional_synthetic_series_preserves_intensity_and_geometry(tmp_path):
    sitk = pytest.importorskip("SimpleITK")
    from mirai_ct.dicom_intake import convert_series
    from mirai_ct.volume import load_volume, read_slice

    source = tmp_path / "dicom"
    source.mkdir()
    writer = sitk.ImageFileWriter()
    writer.KeepOriginalImageUIDOn()
    uid = "1.2.826.0.1.3680043.10.543.20261115.1"
    for k in range(3):
        image = sitk.GetImageFromArray(np.full((4, 5), 10 + k, dtype=np.int16))
        image.SetSpacing([0.6, 0.8])
        for tag, value in {
            "0008|0060": "CT",
            "0020|000e": uid,
            "0020|000d": "1.2.826.0.1.3680043.10.543.20261115",
            "0020|0032": f"-20\\30\\{10 + 2.5 * k}",
            "0020|0037": "1\\0\\0\\0\\1\\0",
            "0028|0030": "0.8\\0.6",
            "0028|1052": "0",
            "0028|1053": "1",
            "0028|1054": "HU",
            "0020|0013": str(k + 1),
        }.items():
            image.SetMetaData(tag, value)
        writer.SetFileName(str(source / f"slice-{k}.dcm"))
        writer.Execute(image)
    output = tmp_path / "converted"
    convert_series(source, output, expected_series_uid=uid)
    result = load_volume(output / "ct.nii.gz")
    assert result.shape == (5, 4, 3)
    for k in range(3):
        np.testing.assert_array_equal(read_slice(result, 2, k), 10 + k)
    np.testing.assert_allclose(
        result.affine, [[-0.6, 0, 0, 20], [0, -0.8, 0, -30], [0, 0, 2.5, 10], [0, 0, 0, 1]]
    )
    with pytest.raises(ValueError, match="exists"):
        convert_series(source, output, expected_series_uid=uid)
