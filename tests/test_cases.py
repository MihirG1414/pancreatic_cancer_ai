import pytest

from mirai_ct.cases import read_cases


def test_local_csv_resolves_relative_paths_and_optional_label(tmp_path):
    manifest = tmp_path / "cases.csv"
    manifest.write_text(
        "case_id,scan_path,label_path,dataset_source\n"
        'synthetic-test,"data/scan,one.nii.gz",,synthetic software test\n',
        encoding="utf-8-sig",
    )
    cases = read_cases(manifest)
    assert len(cases) == 1
    assert cases[0].scan_path == tmp_path / "data/scan,one.nii.gz"
    assert cases[0].label_path is None
    assert cases[0].dataset_source == "synthetic software test"


@pytest.mark.parametrize(
    "rows",
    [
        "case_id,scan_path\na,b\n",
        "case_id,scan_path,label_path,dataset_source\na,b,,\n",
        "case_id,scan_path,label_path,dataset_source\na,b,,test\na,c,,test\n",
        "case_id,scan_path,label_path,dataset_source\n,b,,test\n",
        "case_id,scan_path,label_path,dataset_source\na,b,,test,extra\n",
    ],
)
def test_invalid_manifest_rejected(tmp_path, rows):
    path = tmp_path / "bad.csv"
    path.write_text(rows)
    with pytest.raises(ValueError):
        read_cases(path)


def test_empty_template_is_not_a_real_case(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("case_id,scan_path,label_path,dataset_source\n")
    assert read_cases(path) == []
