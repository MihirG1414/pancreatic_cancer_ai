# Paste this complete cell below the existing successful Colab notebook.
# Reuses the current runtime, input and checkpoints; does not rerun setup.
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

from google.colab import files

_tools_revision = "f49a766e753160829c0c8f9be0ba93fdd269a72e"
_root = Path("/content/mirai-panorama")
_python = _root / "gpu-env/bin/python"
_run = _root / "run-20261115-124314"
_input = _root / "input-cptac-pilot-01"
_output = _root / "explanation-cptac-pilot-01-v2"
_journal = _output / "explanation.json"
_tools = _root / ("explanation-tools-" + _tools_revision[:12])
if not _python.is_file() or not (_run / "bundle/run.json").is_file():
    raise RuntimeError("Original Colab runtime/run is missing; do not reinstall or rerun blindly.")
_run_info = json.loads((_run / "bundle/run.json").read_text())
_input_info = json.loads((_input / "input-provenance.json").read_text())
if (
    _run_info.get("status") != "success"
    or _input_info.get("case_id") != "cptac_pilot_01"
    or _run_info.get("source_sha256") != _input_info.get("source_sha256")
):
    raise RuntimeError("Expected completed second CT run and its matching input.")
_env = dict(os.environ, GIT_LFS_SKIP_SMUDGE="1")
if not _tools.exists():
    subprocess.run(["git", "init", str(_tools)], check=True, env=_env)
    subprocess.run(
        [
            "git",
            "-C",
            str(_tools),
            "remote",
            "add",
            "origin",
            "https://github.com/MihirG1414/pancreatic_cancer_ai.git",
        ],
        check=True,
        env=_env,
    )
subprocess.run(
    ["git", "-C", str(_tools), "fetch", "--depth", "1", "origin", _tools_revision],
    check=True,
    env=_env,
)
subprocess.run(
    ["git", "-C", str(_tools), "checkout", "--detach", "FETCH_HEAD"], check=True, env=_env
)
_actual = subprocess.check_output(
    ["git", "-C", str(_tools), "rev-parse", "HEAD"], text=True
).strip()
if _actual != _tools_revision:
    raise RuntimeError("Explanation source pin mismatch.")
_env.update(
    PYTHONPATH=str(_tools / "src"),
    MPLBACKEND="Agg",
    PYTHONDONTWRITEBYTECODE="1",
    PATH=str(_python.parent) + os.pathsep + os.environ["PATH"],
)
_log = _root / "explanation-cptac-pilot-01-v2.log"
print("Explaining:", _run)
print(
    "Two unchanged controls and eight occlusions; original predictions and weights are preserved."
)
print("Log:", _log, flush=True)
with _log.open("a", encoding="utf-8") as _console:
    _process = subprocess.Popen(
        [
            str(_python),
            "-u",
            "-m",
            "mirai_ct.panorama_explain",
            "--root",
            str(_root),
            "--baseline",
            str(_root / "baseline"),
            "--run-dir",
            str(_run),
            "--input",
            str(_input),
            "--output",
            str(_output),
        ],
        env=_env,
        stdout=_console,
        stderr=subprocess.STDOUT,
    )
    _shown = -1
    while _process.poll() is None:
        if _journal.is_file():
            _state = json.loads(_journal.read_text())
            _done = len(_state.get("blocks", []))
            if _done != _shown:
                print("Completed occlusions:", _done, "/ 8", flush=True)
                _shown = _done
        time.sleep(10)
print(_log.read_text(errors="replace")[-12000:])
if _process.returncode:
    raise RuntimeError(f"Explanation stopped with exit {_process.returncode}; inspect {_log}.")
_state = json.loads(_journal.read_text())
if _state.get("status") != "success" or len(_state.get("blocks", [])) != 8:
    raise RuntimeError("A complete explanation was not produced.")
_download = _root / "panorama-explanation-cptac-pilot-01-v2.json"
shutil.copyfile(_journal, _download)
print("Download genuine explanation:", _download)
files.download(str(_download))
