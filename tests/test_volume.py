"""Synthetic arrays test software behavior, never cancer detection."""

import nibabel as nib
import numpy as np
import pytest

from mirai_ct.volume import check_geometry, load_volume, metadata, read_slice


def write_image(tmp_path, name="scan.nii.gz", shape=(8, 9, 10), affine=None):
    data = np.arange(np.prod(shape), dtype=np.int16).reshape(shape)
    image = nib.Nifti1Image(data, np.diag([0.8, 0.9, 2.5, 1]) if affine is None else affine)
    image.header.set_xyzt_units("mm")
    path = tmp_path / name
    nib.save(image, path)
    return path, data


@pytest.mark.parametrize("extension", [".nii", ".nii.gz"])
def test_metadata_and_slice_preserve_geometry_and_remain_lazy(tmp_path, extension):
    path, data = write_image(tmp_path, "scan" + extension)
    image = load_volume(path)
    affine = image.affine.copy()
    info = metadata(image)
    assert info["shape"] == [8, 9, 10]
    assert info["spacing"] == pytest.approx([0.8, 0.9, 2.5])
    assert info["orientation"] == ["R", "A", "S"]
    assert info["spatial_units"] == "mm"
    for axis in range(3):
        actual = read_slice(image, axis, 2)
        assert actual.dtype == np.float32
        np.testing.assert_array_equal(actual, np.take(data, 2, axis=axis))
    assert not image.in_memory
    np.testing.assert_array_equal(image.affine, affine)


def test_scaling_applies_to_slice(tmp_path):
    path, data = write_image(tmp_path)
    image = nib.Nifti1Image(data, np.eye(4))
    image.header.set_slope_inter(2, -1000)
    nib.save(image, path)
    np.testing.assert_array_equal(read_slice(load_volume(path), 2, 4), data[:, :, 4] * 2 - 1000)


@pytest.mark.parametrize("axis,index", [(-1, 0), (3, 0), (2, -1), (2, 10)])
def test_invalid_slice_rejected(tmp_path, axis, index):
    path, _ = write_image(tmp_path)
    with pytest.raises(ValueError):
        read_slice(load_volume(path), axis, index)


def test_non_3d_rejected(tmp_path):
    path, _ = write_image(tmp_path, shape=(8, 9, 10, 2))
    with pytest.raises(ValueError, match="3D"):
        load_volume(path)


def test_missing_and_wrong_file_type(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_volume(tmp_path / "missing.nii")
    path = tmp_path / "scan.txt"
    path.write_text("not a scan")
    with pytest.raises(ValueError, match="NIfTI"):
        load_volume(path)


def test_matching_geometry(tmp_path):
    path, _ = write_image(tmp_path)
    check_geometry(load_volume(path), load_volume(path))


@pytest.mark.parametrize("change", ["translation", "flip", "spacing", "shape", "units"])
def test_mask_geometry_mismatch_rejected(tmp_path, change):
    path, _ = write_image(tmp_path)
    scan = load_volume(path)
    affine = scan.affine.copy()
    shape = scan.shape
    if change == "translation":
        affine[0, 3] += 1
    elif change == "flip":
        affine[0, 0] *= -1
    elif change == "spacing":
        affine[2, 2] *= 2
    elif change == "shape":
        shape = (8, 9, 11)
    label_path, _ = write_image(tmp_path, "mask.nii.gz", shape, affine)
    label = load_volume(label_path)
    if change == "units":
        label.header.set_xyzt_units("meter")
    with pytest.raises(ValueError, match="geometry"):
        check_geometry(scan, label)


def test_uncertain_geometry_reported_and_overlay_blocked(tmp_path):
    path, _ = write_image(tmp_path)
    image = load_volume(path)
    image.header.set_xyzt_units("unknown")
    assert metadata(image)["warnings"]
    with pytest.raises(ValueError, match="geometry"):
        check_geometry(image, image)


def test_conflicting_transforms_reported_and_overlay_blocked(tmp_path):
    path, _ = write_image(tmp_path)
    image = load_volume(path)
    shifted = image.affine.copy()
    shifted[0, 3] += 5
    image.set_qform(shifted, code=1)
    assert any("qform" in warning for warning in metadata(image)["warnings"])
    with pytest.raises(ValueError, match="geometry"):
        check_geometry(image, image)


def test_truncated_voxel_payload_is_explicit(tmp_path):
    path, _ = write_image(tmp_path, "truncated.nii")
    with path.open("r+b") as stream:
        stream.truncate(400)
    with pytest.raises(ValueError, match="truncated or corrupt"):
        read_slice(load_volume(path), 2, 9)


def test_slice_never_materializes_whole_proxy(tmp_path, monkeypatch):
    path, _ = write_image(tmp_path)
    image = load_volume(path)

    def forbidden(*args, **kwargs):
        raise AssertionError("Full proxy conversion must not occur")

    monkeypatch.setattr(nib.arrayproxy.ArrayProxy, "__array__", forbidden)
    assert read_slice(image, 2, 3).shape == (8, 9)


def test_low_memory_warning_is_visible(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import psutil

    path, _ = write_image(tmp_path)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(available=400 * 1024**2))
    with pytest.warns(UserWarning, match="512 MiB"):
        read_slice(load_volume(path), 2, 3)


def test_memory_budget_rejects_slice(tmp_path, monkeypatch):
    from types import SimpleNamespace

    import psutil

    path, _ = write_image(tmp_path)
    monkeypatch.setattr(psutil, "virtual_memory", lambda: SimpleNamespace(available=1))
    with pytest.raises(MemoryError, match="memory budget"):
        read_slice(load_volume(path), 2, 3)
