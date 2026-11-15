"""One-command handoff tested only with clearly synthetic fixture bundles."""

import json
import zipfile

import pytest


def test_build_demo_from_zip_preserves_source_and_reports_missing_products(tmp_path):
    from test_panorama import bundle_fixture

    from mirai_ct.demo import build_demo
    from mirai_ct.panorama_io import sha256_file

    case, exported, bundle, _ = bundle_fixture(tmp_path)
    archive = tmp_path / "input.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in bundle.rglob("*"):
            if path.is_file():
                z.write(path, path.relative_to(bundle).as_posix())
    before = sha256_file(case.scan_path)
    report = build_demo(case, exported, archive, tmp_path / "demo")
    info = json.loads((report.parent / "report.json").read_text())
    assert not info["model_segmentation_available"]
    assert (report.parent / "viewer/slices/0-ct.png").is_file()
    assert (tmp_path / "demo/demo-report.zip").is_file()
    assert sha256_file(case.scan_path) == before
    with zipfile.ZipFile(tmp_path / "demo/demo-report.zip") as z:
        assert "index.html" in z.namelist()
        assert not any(name.endswith((".nii.gz", ".mha")) for name in z.namelist())
    with pytest.raises(ValueError, match="exists"):
        build_demo(case, exported, archive, tmp_path / "demo")


@pytest.mark.parametrize("bad", ["../run.json", "C:/run.json", "run.json", "run.json."])
def test_demo_zip_rejects_traversal_and_duplicate_members(tmp_path, bad):
    from mirai_ct.demo import extract_bundle

    archive = tmp_path / "unsafe.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("run.json", "{}")
        if bad == "run.json":
            with pytest.warns(UserWarning):
                z.writestr(bad, "{}")
        else:
            z.writestr(bad, "{}")
    with pytest.raises(ValueError):
        extract_bundle(archive, tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()


def test_request_for_complete_products_rejects_old_bundle(tmp_path):
    from test_panorama import bundle_fixture

    from mirai_ct.demo import build_demo

    case, exported, bundle, _ = bundle_fixture(tmp_path)
    with pytest.raises(ValueError, match="lacks actual"):
        build_demo(case, exported, bundle, tmp_path / "demo", require_model_products=True)
    assert not (tmp_path / "demo/report").exists()
    assert json.loads((tmp_path / "demo/demo-failure.json").read_text())["status"] == "failed"


def test_oversized_zip_metadata_rejected_before_extracting(tmp_path):
    from mirai_ct.demo import extract_bundle

    archive = tmp_path / "oversized.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("run.json", " " * (1024**2 + 1))
    with pytest.raises(ValueError, match="metadata budget"):
        extract_bundle(archive, tmp_path / "bundle")
    assert not (tmp_path / "bundle").exists()
