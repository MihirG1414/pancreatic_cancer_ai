"""Analytical contours and synthetic DICOM metadata; not clinical validation."""

import json

import nibabel as nib
import numpy as np
import pytest

pydicom = pytest.importorskip("pydicom")
Dataset = pydicom.dataset.Dataset
FileDataset = pydicom.dataset.FileDataset
FileMetaDataset = pydicom.dataset.FileMetaDataset
CTImageStorage = pydicom.uid.CTImageStorage
ExplicitVRLittleEndian = pydicom.uid.ExplicitVRLittleEndian
RTStructureSetStorage = pydicom.uid.RTStructureSetStorage


def test_polygon_sampling_centers_boundary_and_reversed_winding():
    from mirai_ct.rtstruct import polygon_mask

    square = np.array([[1, 1], [3, 1], [3, 3], [1, 3]], dtype=float)
    mask = polygon_mask(square, (6, 5))
    expected = np.zeros((6, 5), dtype=bool)
    expected[1:4, 1:4] = True
    np.testing.assert_array_equal(mask, expected)
    np.testing.assert_array_equal(polygon_mask(square[::-1], (6, 5)), expected)


def test_keyhole_preserves_excluded_inner_centers():
    from mirai_ct.rtstruct import polygon_mask

    # Outer square and inner square joined by a retraced, zero-width channel.
    keyhole = np.array(
        [[0, 0], [6, 0], [6, 6], [0, 6], [0, 0], [2, 2], [2, 4], [4, 4], [4, 2], [2, 2], [0, 0]],
        dtype=float,
    )
    mask = polygon_mask(keyhole, (7, 7))
    assert mask[1, 1] and not mask[3, 3]
    assert mask[2, 3]  # Boundary points belong to the contour.


def fixture(tmp_path):
    from mirai_ct.panorama_io import sha256_file

    ct_dir = tmp_path / "dicom"
    ct_dir.mkdir()
    affine = np.array([[0, -2, 0, 20], [1.5, 0, 0, -30], [0, 0, -3, 40], [0, 0, 0, 1]])
    lps_affine = np.diag([-1, -1, 1, 1]) @ affine
    image = nib.Nifti1Image(np.zeros((8, 9, 3), dtype=np.int16), affine)
    image.header.set_xyzt_units("mm")
    ct = tmp_path / "ct.nii.gz"
    nib.save(image, ct)
    series, study, frame = [f"1.2.826.0.1.3680043.10.543.7.{k}" for k in (1, 2, 3)]
    sop_uids = []
    for k in range(3):
        sop = f"1.2.826.0.1.3680043.10.543.7.4.{k + 1}"
        sop_uids.append(sop)
        meta = FileMetaDataset()
        meta.TransferSyntaxUID = ExplicitVRLittleEndian
        meta.MediaStorageSOPClassUID = CTImageStorage
        meta.MediaStorageSOPInstanceUID = sop
        ds = FileDataset(str(ct_dir / f"{k}.dcm"), {}, file_meta=meta, preamble=b"\0" * 128)
        ds.SOPClassUID, ds.SOPInstanceUID = CTImageStorage, sop
        ds.SeriesInstanceUID, ds.StudyInstanceUID, ds.FrameOfReferenceUID = series, study, frame
        ds.Modality = "CT"
        ds.Rows, ds.Columns = 9, 8
        ds.ImagePositionPatient = (lps_affine @ [0, 0, k, 1])[:3].tolist()
        ds.ImageOrientationPatient = [0, -1, 0, 1, 0, 0]
        ds.PixelSpacing = [2, 1.5]
        ds.save_as(ds.filename, enforce_file_format=True)
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = RTStructureSetStorage
    meta.MediaStorageSOPInstanceUID = "1.2.826.0.1.3680043.10.543.7.5"
    rt = FileDataset(str(tmp_path / "roi.dcm"), {}, file_meta=meta, preamble=b"\0" * 128)
    rt.SOPClassUID, rt.SOPInstanceUID = RTStructureSetStorage, meta.MediaStorageSOPInstanceUID
    rt.Modality = "RTSTRUCT"
    roi = Dataset()
    roi.ROINumber = 7
    roi.ROIName = "SYNTHETIC ROI"
    roi.ReferencedFrameOfReferenceUID = frame
    rt.StructureSetROISequence = [roi]
    rframe = Dataset()
    rframe.FrameOfReferenceUID = frame
    rstudy = Dataset()
    rstudy.ReferencedSOPInstanceUID = study
    rseries = Dataset()
    rseries.SeriesInstanceUID = series
    rstudy.RTReferencedSeriesSequence = [rseries]
    rframe.RTReferencedStudySequence = [rstudy]
    rt.ReferencedFrameOfReferenceSequence = [rframe]
    contour = Dataset()
    contour.ContourGeometricType = "CLOSED_PLANAR"
    contour.NumberOfContourPoints = 4
    points = np.array([[1, 2, 1, 1], [3, 2, 1, 1], [3, 4, 1, 1], [1, 4, 1, 1]])
    contour.ContourData = (points @ lps_affine.T)[:, :3].ravel().tolist()
    ref = Dataset()
    ref.ReferencedSOPInstanceUID = sop_uids[1]
    ref.ReferencedSOPClassUID = CTImageStorage
    contour.ContourImageSequence = [ref]
    rc = Dataset()
    rc.ReferencedROINumber = 7
    rc.ContourSequence = [contour]
    rt.ROIContourSequence = [rc]
    rt.save_as(rt.filename, enforce_file_format=True)
    conversion = tmp_path / "conversion.json"
    conversion.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "series_uid": series,
                "nifti_sha256": sha256_file(ct),
                "source_dicom_sha256": {p.name: sha256_file(p) for p in ct_dir.glob("*.dcm")},
            }
        )
    )
    return ct, ct_dir, rt, conversion


def test_rtstruct_round_trip_matches_native_reflected_grid(tmp_path):
    from mirai_ct.panorama_io import sha256_file
    from mirai_ct.rtstruct import convert_rtstruct
    from mirai_ct.volume import check_geometry, load_volume, read_slice

    ct, dicom, rt, conversion = fixture(tmp_path)
    before = sha256_file(ct)
    result = convert_rtstruct(
        ct,
        dicom,
        tmp_path / "roi.dcm",
        conversion,
        tmp_path / "out",
        roi_number=7,
        description="Synthetic reference",
    )
    mask = load_volume(result)
    check_geometry(load_volume(ct), mask)
    expected = np.zeros((8, 9), dtype=np.float32)
    expected[1:4, 2:5] = 1
    np.testing.assert_array_equal(read_slice(mask, 2, 1), expected)
    assert np.count_nonzero(read_slice(mask, 2, 0)) == 0
    assert sha256_file(ct) == before
    info = json.loads((result.parent / "reference.json").read_text())
    assert info["voxel_count"] == 9
    assert info["reference_volume_ml"] == pytest.approx(0.081)
    assert info["inference_executed"] is False
    with pytest.raises(ValueError, match="exists"):
        convert_rtstruct(
            ct,
            dicom,
            tmp_path / "roi.dcm",
            conversion,
            tmp_path / "out",
            roi_number=7,
            description="Synthetic reference",
        )


@pytest.mark.parametrize(
    "bad",
    ["frame", "series", "sop", "plane", "open", "nan", "roi", "ct_tamper", "dicom_tamper", "slab"],
)
def test_rtstruct_rejects_unsafe_reference(tmp_path, bad):
    from mirai_ct.rtstruct import convert_rtstruct

    ct, dicom, rt, conversion = fixture(tmp_path)
    c = rt.ROIContourSequence[0].ContourSequence[0]
    if bad == "frame":
        rt.StructureSetROISequence[0].ReferencedFrameOfReferenceUID = "1.2.999"
    elif bad == "series":
        rt.ReferencedFrameOfReferenceSequence[0].RTReferencedStudySequence[
            0
        ].RTReferencedSeriesSequence[0].SeriesInstanceUID = "1.2.999"
    elif bad == "sop":
        c.ContourImageSequence[0].ReferencedSOPInstanceUID = "1.2.999"
    elif bad == "plane":
        c.ContourData[2] += 0.5
    elif bad == "open":
        c.ContourGeometricType = "OPEN_PLANAR"
    elif bad == "nan":
        c.ContourData[0] = float("nan")
    elif bad == "slab":
        c.ContourSlabThickness = 2.0
    elif bad == "ct_tamper":
        ct.write_bytes(b"tampered")
    elif bad == "dicom_tamper":
        (dicom / "0.dcm").write_bytes(b"tampered")
    rt.save_as(rt.filename, enforce_file_format=True)
    with pytest.raises((ValueError, OSError)):
        convert_rtstruct(
            ct,
            dicom,
            tmp_path / "roi.dcm",
            conversion,
            tmp_path / "out",
            roi_number=99 if bad == "roi" else 7,
            description="Synthetic reference",
        )
    assert not (tmp_path / "out").exists()


def test_source_provenance_binds_report_semantics_to_exact_ct_and_mask(tmp_path):
    from mirai_ct.cases import Case
    from mirai_ct.report import generate_report
    from mirai_ct.rtstruct import convert_rtstruct

    ct, dicom, rt, conversion = fixture(tmp_path)
    path = convert_rtstruct(
        ct,
        dicom,
        tmp_path / "roi.dcm",
        conversion,
        tmp_path / "out",
        roi_number=7,
        description="Explicit synthetic source reference",
    )
    provenance = path.parent / "reference.json"
    case = Case("synthetic", ct, path, "Synthetic reference software check")
    report = generate_report(case, tmp_path / "report", annotation_provenance=provenance)
    text = report.read_text(encoding="utf-8")
    assert "Explicit synthetic source reference" in text
    assert "Reference provenance checked against CT and mask SHA256" in text
    info = json.loads(provenance.read_text())
    info["reference_sha256"] = "0" * 64
    provenance.write_text(json.dumps(info))
    with pytest.raises(ValueError, match="checksum"):
        generate_report(case, tmp_path / "rejected", annotation_provenance=provenance)
    assert not (tmp_path / "rejected").exists()


def test_xor_hole_and_mixed_contours_fail_closed(tmp_path):
    from copy import deepcopy

    from mirai_ct.rtstruct import convert_rtstruct
    from mirai_ct.volume import load_volume, read_slice

    ct, dicom, rt, conversion = fixture(tmp_path)
    outer = rt.ROIContourSequence[0].ContourSequence[0]
    outer.ContourGeometricType = "CLOSEDPLANAR_XOR"
    inner = deepcopy(outer)
    outer_points = np.array([[0, 0, 1, 1], [6, 0, 1, 1], [6, 6, 1, 1], [0, 6, 1, 1]])
    inner_points = np.array([[2, 2, 1, 1], [4, 2, 1, 1], [4, 4, 1, 1], [2, 4, 1, 1]])
    affine_lps = np.diag([-1, -1, 1, 1]) @ load_volume(ct).affine
    outer.ContourData = (outer_points @ affine_lps.T)[:, :3].ravel().tolist()
    inner.ContourData = (inner_points @ affine_lps.T)[:, :3].ravel().tolist()
    rt.ROIContourSequence[0].ContourSequence = [outer, inner]
    rt.save_as(rt.filename, enforce_file_format=True)
    path = convert_rtstruct(
        ct,
        dicom,
        tmp_path / "roi.dcm",
        conversion,
        tmp_path / "xor",
        roi_number=7,
        description="Synthetic XOR reference",
    )
    mask = read_slice(load_volume(path), 2, 1)
    assert mask.sum() == 40  # 49 center samples in outer, minus 9 in inner.
    assert mask[1, 1] and not mask[3, 3]
    inner.ContourGeometricType = "CLOSED_PLANAR"
    rt.save_as(rt.filename, enforce_file_format=True)
    with pytest.raises(ValueError, match="consistent closed"):
        convert_rtstruct(
            ct,
            dicom,
            tmp_path / "roi.dcm",
            conversion,
            tmp_path / "mixed",
            roi_number=7,
            description="Synthetic invalid mix",
        )
    assert not (tmp_path / "mixed").exists()
