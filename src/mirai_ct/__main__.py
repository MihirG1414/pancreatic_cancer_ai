"""Command line entry point: python -m mirai_ct --help."""

import argparse
import json
import sys
from pathlib import Path

from mirai_ct.volume import check_geometry, load_volume, memory_status, metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Mirai CPU CT inspection; no inference.")
    parser.add_argument("scan", type=Path, help="One .nii or .nii.gz CT")
    parser.add_argument("--mask", type=Path, help="Optional existing annotation")
    parser.add_argument("--axis", type=int, choices=[0, 1, 2], default=2)
    parser.add_argument("--index", type=int, help="Native slice index; defaults to middle")
    parser.add_argument("--level", type=float, default=50)
    parser.add_argument("--window", type=float, default=400)
    parser.add_argument("--output", type=Path, help="Save a local PNG; no window opens")
    args = parser.parse_args()
    try:
        before = memory_status()
        scan = load_volume(args.scan)
        mask = load_volume(args.mask) if args.mask else None
        if mask is not None:
            check_geometry(scan, mask)
        print(
            json.dumps(
                {
                    "scan": metadata(scan),
                    "memory_before": before,
                    "mask_geometry": "matched" if mask is not None else "not supplied",
                },
                indent=2,
            )
        )
        if args.output:
            if args.output.suffix.lower() != ".png":
                raise ValueError("Use a .png output path, preferably under outputs/.")
            if args.output.exists():
                raise ValueError("Output already exists; choose a new name to preserve it.")
            import matplotlib

            matplotlib.use("Agg")
            import matplotlib.pyplot as plt

            from mirai_ct.visualization import plot_slice

            fig = plot_slice(scan, args.axis, args.index, mask, args.level, args.window)
            try:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(args.output, dpi=120)
            finally:
                plt.close(fig)
        print(
            json.dumps(
                {"memory_after": memory_status(), "full_volume_cached": scan.in_memory}, indent=2
            )
        )
        return 0
    except (OSError, ValueError, MemoryError) as exc:
        print(f"Inspection failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
