import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pytest

from mirai_ct.visualization import plot_slice
from mirai_ct.volume import load_volume


def images(tmp_path):
    scan = nib.Nifti1Image(np.zeros((12, 14, 8), dtype=np.int16), np.diag([1, 2, 3, 1]))
    labels = np.zeros(scan.shape, dtype=np.uint8)
    labels[3:8, 4:9, 4] = 2
    mask = nib.Nifti1Image(labels, scan.affine)
    for name, image in [("scan", scan), ("mask", mask)]:
        image.header.set_xyzt_units("mm")
        nib.save(image, tmp_path / (name + ".nii.gz"))
    return load_volume(tmp_path / "scan.nii.gz"), load_volume(tmp_path / "mask.nii.gz")


def test_existing_mask_overlay_and_physical_aspect(tmp_path):
    scan, mask = images(tmp_path)
    fig = plot_slice(scan, axis=2, index=4, mask=mask)
    assert len(fig.axes) == 2
    assert fig.axes[0].get_aspect() == 2
    np.testing.assert_array_equal(
        fig.axes[1].images[1].get_array().mask, np.asarray(mask.dataobj[:, :, 4]).T == 0
    )
    assert "not prediction" in fig.axes[1].get_title()
    fig.savefig(tmp_path / "synthetic-software-check.png")
    assert not scan.in_memory and not mask.in_memory
    plt.close(fig)


def test_overlay_mismatch_refuses_to_render(tmp_path):
    scan, mask = images(tmp_path)
    mask.affine[0, 3] += 10
    with pytest.raises(ValueError, match="geometry"):
        plot_slice(scan, axis=2, index=4, mask=mask)


@pytest.mark.parametrize("window", [0, -1, float("nan")])
def test_invalid_window(tmp_path, window):
    scan, _ = images(tmp_path)
    with pytest.raises(ValueError, match="window"):
        plot_slice(scan, axis=2, index=4, window=window)


def test_noninteger_annotation_rejected(tmp_path):
    scan, _ = images(tmp_path)
    mask = nib.Nifti1Image(np.full(scan.shape, 0.5, dtype=np.float32), scan.affine)
    mask.header.set_xyzt_units("mm")
    with pytest.raises(ValueError, match="integer"):
        plot_slice(scan, axis=2, index=4, mask=mask)
