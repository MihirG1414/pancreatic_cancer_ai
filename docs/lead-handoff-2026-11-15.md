# Deferred clinical requirements for the lead

The current deliverable is a working offline research demonstration of the
pretrained PANORAMA pipeline on two public CT examples. The following work is
deferred because it requires permitted data, clinical reference information or
qualified review that is unavailable for the 16 November review.

## Draft request to the lead

Please help arrange:

1. A permitted, de-identified CT evaluation cohort containing confirmed PDAC and
   confirmed non-PDAC patients, with the diagnosis/reference standard recorded.
   Empty segmentation masks are insufficient to establish non-PDAC status.
2. An audit of overlap with PANORAMA training/development data and a patient-level
   split. MSD/NIH examples cannot automatically be called independent; using a
   different collection name alone is also insufficient.
3. Radiologist review of CT phase/suitability, candidate placement, missed areas,
   model-mask boundaries and source annotations. For head/body/tail reporting,
   provide or review an aligned anatomical subregion mask, or assess a separately
   validated anatomy model. The software accepts explicit labels/provenance.
4. An agreed evaluation protocol: eligible CT phase/population, diagnosis and
   lesion references, operating threshold chosen separately from the test set,
   lesion matching, required sample size/uncertainty analysis and error review.
5. Confirmation of permitted data/model use for any company deployment. The
   current PANORAMA weight-use declaration covers the permitted research run;
   it does not establish commercial-use permission or clinical clearance.

The software is ready to calculate source overlap, lesion matching and explicitly
labeled case-score metrics. Clinical conclusions must wait for those inputs and
reviews. Please keep patient identifiers, source documents, scans, weights and
local manifests out of Git and public channels.

This is a request draft only; no message has been sent to the lead.
