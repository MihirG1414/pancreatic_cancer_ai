"""Execute the inspection notebook locally; never commit populated outputs."""

import argparse
from pathlib import Path

import nbformat
from nbclient import NotebookClient


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("outputs/inspection.executed.ipynb"))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    output = args.output.resolve()
    if not output.is_relative_to(root / "outputs"):
        parser.error(
            "Executed notebooks must stay under this project's ignored outputs/ directory."
        )
    if output.exists():
        parser.error("Output exists; choose a new filename to preserve the earlier run.")
    notebook = nbformat.read(root / "notebooks/01_inspect_ct.ipynb", as_version=4)
    NotebookClient(
        notebook, timeout=180, kernel_name="mirai-ct", resources={"metadata": {"path": str(root)}}
    ).execute()
    output.parent.mkdir(parents=True, exist_ok=True)
    nbformat.write(notebook, output)
    print(f"Executed successfully: {output}")


if __name__ == "__main__":
    main()
