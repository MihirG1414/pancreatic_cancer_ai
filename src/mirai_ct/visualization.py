"""Native voxel-plane inspection; labels are existing annotations, not predictions."""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Patch

from mirai_ct.volume import Volume, check_geometry, metadata, read_slice


def plot_slice(
    scan: Volume,
    axis: int = 2,
    index: int | None = None,
    mask: Volume | None = None,
    level: float = 50,
    window: float = 400,
    prediction: Volume | None = None,
) -> Figure:
    """Plot one plane, respecting pixel spacing; never reorient/resample a volume."""
    if not np.isfinite(window) or window <= 0 or not np.isfinite(level):
        raise ValueError("Display window must be finite and positive; level must be finite.")
    if axis not in (0, 1, 2):
        raise ValueError("Slice axis must be 0, 1 or 2.")
    if mask is not None:
        check_geometry(scan, mask)
    if prediction is not None:
        check_geometry(scan, prediction)
    index = scan.shape[axis] // 2 if index is None else index
    plane = read_slice(scan, axis, index)
    label_plane = read_slice(mask, axis, index) if mask is not None else None
    prediction_plane = read_slice(prediction, axis, index) if prediction is not None else None
    if prediction_plane is not None and (prediction_plane.min() < 0 or prediction_plane.max() > 1):
        raise ValueError("Candidate detection values must be in [0,1].")
    if label_plane is not None and (
        (label_plane < 0).any()
        or (label_plane > 65535).any()
        or not np.equal(label_plane, np.floor(label_plane)).all()
    ):
        raise ValueError("Existing mask must contain nonnegative integer label IDs <= 65535.")
    info = metadata(scan)
    horizontal, vertical = [i for i in range(3) if i != axis]
    spacing = info["affine_spacing"]
    aspect = spacing[vertical] / spacing[horizontal]
    panels = 1 + int(mask is not None) + int(prediction is not None)
    fig, axes = plt.subplots(1, panels, figsize=(5 * panels, 5), squeeze=False)
    for ax in axes.flat:
        ax.imshow(
            plane.T,
            origin="lower",
            cmap="gray",
            interpolation="nearest",
            vmin=level - window / 2,
            vmax=level + window / 2,
            aspect=aspect,
        )
        ax.set_xlabel(f"Voxel axis {horizontal} (+{info['orientation'][horizontal]})")
        ax.set_ylabel(f"Voxel axis {vertical} (+{info['orientation'][vertical]})")
    axes[0, 0].set_title("CT: stored scaled intensities")
    if label_plane is not None:
        ax = axes[0, 1]
        ids = np.unique(label_plane[label_plane > 0]).astype(int)
        if len(ids):
            color_map = plt.get_cmap("tab10", len(ids))
            colors = np.ma.masked_where(label_plane.T == 0, np.searchsorted(ids, label_plane.T))
            ax.imshow(
                colors,
                origin="lower",
                cmap=color_map,
                interpolation="nearest",
                vmin=-0.5,
                vmax=len(ids) - 0.5,
                alpha=0.45,
                aspect=aspect,
            )
            ax.legend(
                handles=[
                    Patch(color=color_map(i), label=f"Label {value}") for i, value in enumerate(ids)
                ],
                loc="upper right",
            )
        ax.set_title(
            "Existing annotation (not prediction)"
            + ("\nNo labels on slice" if not len(ids) else "")
        )
    if prediction_plane is not None:
        ax = axes[0, -1]
        overlay = ax.imshow(
            np.ma.masked_less_equal(prediction_plane.T, 0),
            origin="lower",
            cmap="magma",
            interpolation="nearest",
            vmin=0,
            vmax=1,
            alpha=0.65,
            aspect=aspect,
        )
        fig.colorbar(overlay, ax=ax, label="Uncalibrated candidate score", shrink=0.65)
        ax.set_title(
            "PANORAMA candidate detection map"
            + ("\nNo candidate values on slice" if prediction_plane.max() == 0 else "")
        )
    fig.suptitle(
        f"Native axis {axis}, slice {index} | level {level:g}, window {window:g}\n"
        "Original geometry; not a standardized anatomical view"
    )
    fig.tight_layout()
    return fig
