# Documentation claim auditor

An offline static auditor comparing documentation promises with Python source call
patterns. It reads root README.md and Markdown beneath any docs path component,
ignores fenced examples, and parses source without executing it. It makes no
network calls, writes no files, and collects no telemetry.

## Install and use

```sh
python3 -m pip install .
multi-receipts-detection-claim-audit audit . --json
python3 -m multi_receipts_detection_claim_audit audit . --verbose
multi-receipts-detection-claim-audit audit . --ignore vendor --ignore build --fail-on medium
multi-receipts-detection-claim-audit --version
python3 -m unittest discover
python3 -m build
```

The repository defaults to the current directory. Ignore prefixes match complete
relative path components; repeat the option for multiple prefixes. The default
failure threshold is high; medium also fails on evidence found only in tests.
Exit codes: 0 for PASS or findings below the threshold, 2 for findings at or above
the threshold, and 1 for usage or I/O errors. JSON includes claims, evidence,
findings and verdict. Verbose text includes locations. One finding is emitted
per claim family. Unsupported positive promises produce HIGH, or MEDIUM when only
tests supply evidence; denials contradicted by production evidence produce HIGH.
With no source, a positive promise fails and a denial passes.

## Exact vocabulary and rules

```text
documented-multi-receipts-detection-claim-false
documented-no-multi-receipts-detection-claim-false
multi receipt detection
detect multi receipts
detects multi receipts
detecting multi receipts
multi receipts detector
multi receipt detector
multi receipts detection
detect multiple receipts
detects multiple receipts
detecting multiple receipts
multiple receipt detection
multiple receipts detection
multiple receipts detector
multiple receipt detector
detect receipts in one image
detects receipts in one image
detecting receipts in one image
detect receipts in a single image
detects receipts in a single image
detecting receipts in a single image
receipt detection
detect receipts
detects receipts
detecting receipts
receipts detector
receipt detector
locate receipts
locates receipts
locating receipts
find receipts in one image
finds receipts in one image
finding receipts in one image
count receipts
counts receipts
counting receipts
receipt counting
count receipts in one image
counts receipts in one image
counting receipts in one image
detect receipt positions
detects receipt positions
detecting receipt positions
receipt positions
locate receipt positions
locates receipt positions
locating receipt positions
receipt bounding boxes
receipts bounding box
detect receipt bounding boxes
multi receipt locator
no multi receipt detection
does not detect multi receipts
does not support multi receipt detection
without multi receipt detection
no multi receipts detector
does not detect multiple receipts
no multiple receipt detection
does not detect receipts
no receipt detection
receipt detection not supported
does not detect receipts in one image
no receipts detector
does not locate receipts
no receipt detector
does not count receipts
no receipt counting
does not find receipts
without receipt detection
no multi receipt detector
does not detect receipt positions
no receipt positions detection
does not support receipt detection
without multi receipts detection
no multiple receipts detector
```

## Source and matching policy

Paragraphs split on blank lines. Matching lowercases, expands contractions,
replaces hyphens with spaces and collapses whitespace. Exact word boundaries,
longest phrases first and alphabetical ties govern matching. Denial spans are
removed before positive matching. Inline code counts; backtick or tilde fences
with at most three leading spaces do not. Symlinked files and directories are
excluded. Source under fixtures, docs and examples is excluded. Tests are tracked
separately. Invalid syntax supplies no evidence. All parts of a route must occur
in one module. Imports resolve aliases; local functions, methods, classes,
assignments, annotated assignments and context-manager bindings shadow imported
names. Dead code counts; untraced alias chains can be missed. This is static
pattern matching, not semantic judgement or a check of runtime credentials.

The following fenced reference documents accepted call names, vendor boundaries,
and matching hazards. It describes the audited vocabulary and its limitations.

```text
Generic names (attribute calls on any base, or imported bare/aliased calls):
detect_multi_receipts
detect_multi_receipt
multi_receipts_detector
multi_receipt_detector
multi_receipts_detection
detect_multiple_receipts
detect_receipts_in_image
detect_receipts
detect_receipt
receipt_detector
receipts_detector
locate_receipts
locate_receipt
find_receipts
find_receipt
count_receipts
count_receipt
receipt_position_detection
detect_receipt_positions
extract_receipt_positions
multi_receipt_detection
receipts_in_image_detection
find_receipts_in_image
locate_receipts_in_image



mindee Client construction + parse call passing MultiReceiptsDetectorV1
(Name exactly MultiReceiptsDetectorV1, or Attribute with attr exactly
MultiReceiptsDetectorV1 such as product.MultiReceiptsDetectorV1 /
mindee.product.MultiReceiptsDetectorV1 /
mindee.product.multi_receipts_detector.MultiReceiptsDetectorV1) as any
argument; import gate mindee. MultiReceiptsDetectorV1 is NOT a 4.x-only
fingerprint (4.22.0 wheel inspected 2026-11-15:
mindee/product/multi_receipts_detector/multi_receipts_detector_v1.py
defines class MultiReceiptsDetectorV1(Inference), endpoint_name
"multi_receipts_detector", endpoint_version "1", exported at top-level
mindee.product and via mindee.product.multi_receipts_detector; its
document is "Multi Receipts Detector API version 1.1" with field
receipts, a list of PositionField, each carrying a polygon /
quadrangle / bounding box of one receipt on the document; there is NO
MultiReceiptsDetectorV2 and no TypeMultiReceiptsDetectorV1 form — the
4.22.0 wheel has no mindee/documents module; the 5.4.0 wheel inspected
2026-11-15 still contains it at
mindee/v1/product/multi_receipts_detector/ — the product survived in
5.x). The tool detects the call in source, not the installed SDK
version. A parse call passing any other product (InvoiceV4, ReceiptV5,
InvoiceSplitterV1, FinancialDocumentV1, PassportV1, BankCheckV1,
BankAccountDetailsV1, BankAccountDetailsV2, PayslipV2, PayslipV3,
NutritionFactsLabelV1, HealthcareCardV1, BusinessCardV1, CustomV1,
GeneratedV1, BillOfLadingV1, ResumeV1, DeliveryNoteV1,
DriverLicenseV1, IdCardV1, InternationalIdV2, CarteGriseV1,
EnergyBillV1, MaterialCertificateV1, BarcodeReaderV1, CropperV1,
UsMailV2, UsMailV3, or any other) is NOT evidence.

## veryfi names (implementation MUST match exactly)

NO veryfi route: the veryfi Python SDK 5.1.0 wheel, inspected
2026-11-15, contains no file or method mentioning "multi receipt"
at all — no multi-receipt detection method exists in the SDK.
NOT evidence: veryfi split_and_process_pdf /
split_and_process_pdf_url (splitting a batched PDF into documents,
the invoice-splitter family's domain); veryfi process_document /
process_any_document and every other veryfi method listed in the
Behaviour section; a call to the non-existent
process_multi_receipts / process_multi_receipts_url /
detect_multi_receipts_document (no such methods exist in the veryfi
SDK); a raw HTTP call to
"https://api.veryfi.com/api/v8/partner/documents" (the generic
Veryfi documents endpoint, shared by receipts, invoices, and other
documents — not multi-receipt-detector-specific).

## azure names (implementation MUST match exactly)

NO azure route: Azure Document Intelligence has no multi-receipt
detector model. The Microsoft Learn v4.0 (GA) prebuilt-model
language-support page and the v4.0 model catalog, searched
2026-11-15 (catalog listing carried from R212), list
prebuilt-read, prebuilt-layout, prebuilt-contract,
prebuilt-healthInsuranceCard.us, prebuilt-idDocument,
prebuilt-invoice, prebuilt-receipt,
prebuilt-marriageCertificate.us, prebuilt-creditCard,
prebuilt-check.us, prebuilt-payStub.us, prebuilt-bankStatement,
prebuilt-mortgage.us.1003/.1004/.1005/.1008/.closingDisclosure,
prebuilt-tax.us.*, prebuilt-vaccinationCard,
prebuilt-businessCard (deprecated in v4.0), and
prebuilt-document — and no model named "multi receipts detector".
A begin_analyze_document call with ANY model id is NOT evidence.
prebuilt-receipt extracts fields from ONE receipt; it does not
return the positions of several receipts in one image.

## google document ai names (implementation MUST match exactly)

NO Google Document AI route: the Document AI processors list /
pretrained overview page, searched 2026-11-15 (carried from
R212), lists pretrained parsers for invoice, expense, bank
statement, pay slip, W2, US driver licence, passport, utility
bill, and identity proofing — an expense parser extracts fields
from one receipt, it does not locate several receipts in one
image, and there is no multi-receipt detector processor, so a
process_document call with ANY processor is NOT evidence.

## eden ai / llamaparse / nanonets / docsumo / other vendor names (implementation MUST match exactly)

NO Eden AI route, by deliberate decision: the standing sibling
rule is that a universal-ai call with ANY model id is NOT
evidence, because the model id is a plain string inside an
arbitrary request payload, not a typed SDK call — the same call
shape serves every Eden AI feature, so there is no fixed static
fingerprint for the call itself. NO LlamaParse route: LlamaParse
is a generative parsing API with no fixed static fingerprint
naming multi-receipt detection. NO Nanonets route: Nanonets
document calls carry an opaque model_id in the URL path (no fixed
fingerprint — the model id is user-configured, not a multi-receipt
detector product). NO Docsumo route: Docsumo uploads go to a
generic endpoint with the document type configured in the
dashboard, not in the call. NO ABBYY Vantage / Rossum / Klippa /
Parseur / Extend route: opaque skill / queue / template /
workflow IDs. NO Textract route: Textract has no multi-receipt
detection operation (analyze_expense covers one document's
expense fields). NO generic object-detection / contour route:
ultralytics YOLO, cv2.findContours, cv2.boundingRect, or any
hand-rolled "find rectangles" step finds shapes, not receipts,
and has no fixed static fingerprint naming receipts. NO receipt
classifier route: classifying a document as a receipt returns one
label, not receipt positions. NO generic "detect document" /
"detect objects" route: a call named detect_document /
detect_objects / document_detector / object_detector with no
"receipt" qualifier could name detecting any document or object,
not receipts. NO mindee v2 extraction API route: configurable
model id, no fixed fingerprint. NO mindee extract_receipts route:
the downstream cropping helper consumes detector output, it does
not perform detection, and its name is generic. NO mindee
InvoiceSplitterV1 route: grouping pages by invoice is not
locating receipts in one image. NO mindee CropperV1 route:
cropping a document region is not detecting receipts.


Matching hazards and limitations:


- The bare phrases "receipt detection" / "detect receipts" /
  "receipt detector" are deliberately MULTIRECEIPTSDETECTION
  phrases: in document-tool docs they almost always name finding
  receipts in an image. But "receipt detection" can also name
  detecting whether a document IS a receipt (receipt
  classification, one label) rather than locating several receipts
  in one image: a doc that means classification, not locating
  receipt positions, is a false positive; the tool flags the claim,
  only the code decides.
- "detect receipts in one image" / "detect receipts in a single
  image" are deliberately phrases: one image holding several
  receipts is the core of this family. But "one image" can also
  name a single receipt photographed alone (the degenerate case):
  a doc that means finding the one receipt in a photo, not
  several, still names the same detection operation (the detector
  returns a list of positions; one receipt is a list of one), so
  this is not a false positive in the operation sense — say so in
  the README.
- "count receipts" / "receipt counting" are deliberately phrases:
  counting how many receipts sit in one image is detection. But
  "count" can also name counting receipt files in a folder (a file
  inventory) rather than detecting receipts in an image: a doc
  that means counting files, not detecting positions, is a false
  positive; the tool flags the claim, only the code decides.
- "receipt positions" / "receipt bounding boxes" are deliberately
  phrases: positions are what the detector returns. But "receipt
  positions" can also name the layout positions of fields inside
  one receipt (where the total sits on the page) rather than the
  positions of several receipts in one image: a doc that means
  field layout, not receipt locations, is a false positive; the
  tool flags the claim, only the code decides.
- "multi receipt detection" / "detect multi receipts" are
  deliberately phrases. But "multi receipt" can also name a single
  document that itself contains several receipts as line items (a
  consolidated expense report) rather than one image holding
  several separate receipts: a doc that means parsing a
  consolidated report, not detecting receipt positions, is a false
  positive; the tool flags the claim, only the code decides.
- "locate receipts" / "find receipts" are deliberately phrases.
  But "find receipts" can also name searching a mailbox or a
  folder for receipt files (retrieval) rather than locating
  receipts inside one image: a doc that means retrieval, not
  detection, is a false positive; the tool flags the claim, only
  the code decides.
- MultiReceiptsDetectorV1 detects positions; detection is locating, not field
  extraction. Each PositionField also has page_id identifying the document page.
  It carries no receipt
  fields (no totals, no merchant names, no dates, no line items).
  A tool that extracts those does so through some other route;
  this family checks for the MultiReceiptsDetectorV1 call, not
  for those fields.
- A generic `detect_receipts(` / `detect_receipt(` /
  `count_receipts(` call can name a string counter for text the
  user typed in rather than an image detector: the tool counts
  the call, the claim plus the code decide — and a subprocess call
  invoking an external CLI is NOT evidence by design, so a thin
  wrapper that only calls subprocess fails.
- Mindee `parse` with MultiReceiptsDetectorV1 counts as evidence:
  the product exists in mindee 4.22.0 (wheel inspected 2026-11-15).
  The tool detects the call in source, not whether the call
  succeeds against a current API version.
- Mindee `parse` with MultiReceiptsDetectorV1 is NOT a 4.x-only
  fingerprint: mindee 5.x kept the multi-receipts detector product
  (5.4.0 wheel inspected 2026-11-15 — it is still present at
  mindee/v1/product/multi_receipts_detector/).
- Mindee `extract_receipts` alone is NOT detected: it is the
  downstream cropping helper that consumes detector output, not
  the detection itself, and its name is generic. Say so in the
  README.
- Mindee `parse` with ReceiptV5 / InvoiceV4 / InvoiceSplitterV1 /
  FinancialDocumentV1 / PassportV1 / BankCheckV1 /
  BankAccountDetailsV1 / BankAccountDetailsV2 / PayslipV2 /
  PayslipV3 / NutritionFactsLabelV1 / HealthcareCardV1 /
  BusinessCardV1 / CustomV1 / GeneratedV1 / BillOfLadingV1 /
  ResumeV1 / DeliveryNoteV1 / DriverLicenseV1 / IdCardV1 /
  InternationalIdV2 / CarteGriseV1 / EnergyBillV1 /
  MaterialCertificateV1 / BarcodeReaderV1 / CropperV1 / UsMailV2 /
  UsMailV3 is NOT detected: those are other document types or
  other operations.
- Mindee `parse` with ReceiptV5 alone is NOT detected even though
  it reads receipts: extracting fields from one receipt is not
  detecting several receipts in one image, and the receipt-only
  route is the receipt family's domain. The same holds for
  InvoiceV4 alone and FinancialDocumentV1 alone. Say so in the
  README.
- Mindee `parse` with InvoiceSplitterV1 is NOT detected: grouping
  pages by invoice is not locating receipts in one image.
- Mindee `parse` with CropperV1 is NOT detected: cropping a
  document region is not detecting receipts.
- Azure `begin_analyze_document` with ANY model id is NOT
  detected: Azure Document Intelligence has no multi-receipt
  detector model (the Learn v4.0 GA prebuilt-model pages list no
  such model, verified 2026-11-15).
- Veryfi has NO multi-receipt detection method: the 5.1.0 wheel
  contains no file or method mentioning "multi receipt"
  (verified 2026-11-15). Veryfi `split_and_process_pdf` /
  `split_and_process_pdf_url` are NOT detected: splitting a
  batched PDF is the invoice-splitter family's domain. Veryfi
  calls of any other kind are NOT detected either. Say so in the
  README.
- Google Document AI `process_document` / `batch_process_documents`
  with ANY processor is NOT detected: Document AI has no
  multi-receipt detector processor (the processors list page
  contains no such processor, verified 2026-11-15). Say so in the
  README.
- Eden AI universal-ai calls with ANY model id are NOT detected:
  the model id is a plain string inside an arbitrary request
  payload, not a typed SDK call, so there is no fixed static
  fingerprint for the call itself.
- LlamaParse calls are NOT detected: its parsing API is
  generative with no fixed static fingerprint naming multi-receipt
  detection.
- Nanonets / Docsumo / ABBYY Vantage / Rossum / Klippa / Parseur /
  Extend calls are NOT detected: opaque model / skill / queue /
  template / workflow IDs, or a generic upload endpoint with the
  document type configured outside the call — no fixed fingerprint.
 
- Textract `analyze_document` / `analyze_expense` / `analyze_id` /
  `start_document_analysis` / `get_expense_analysis` are NOT
  detected: generic document, expense, and identity analysis of
  one document are not multi-receipt detection, and Textract has
  no multi-receipt detection operation.
- Generic object-detection / contour calls (ultralytics YOLO,
  cv2.findContours, cv2.boundingRect, hand-rolled "find
  rectangles") are NOT detected: finding shapes is not finding
  receipts, and there is no fixed static fingerprint naming
  receipts.
- Receipt classifier calls (classify_document, is_receipt, or any
  receipt-classification call) are NOT detected: returning one
  label is not returning receipt positions.
- PDF page-count splits (pypdf / PyPDF2 page slicing, pdfplumber
  page iteration, fitz page extraction, fixed-N-pages chunking)
  are NOT detected: cutting a PDF every N pages does not detect
  receipt positions.
- Generic "detect document" / "detect objects" calls
  (detect_document / detect_objects / document_detector /
  object_detector with no "receipt" qualifier) are NOT detected:
  a bare detection call could name detecting any document or
  object, not receipts.
- A hand-rolled detection from OCR text (`re.search` /
  `re.findall` on extracted text plus manual bounding-box assembly,
  no listed call) is NOT detected: the tool requires a listed call.
 
- The mindee CLI, the veryfi CLI, and any other external
  multi-receipt detector tool invoked through subprocess are NOT
  detected: subprocess calls invoking an external CLI are NOT
  evidence by design.
- Azure Document Intelligence, Mindee, and Veryfi are cloud APIs:
  the tool detects the client call in source, not whether
  credentials are configured or the call succeeds. Say so in the
  README.
- "extract receipts" / "receipt extraction" / "extract receipt
  fields" claims are NOT in the phrase lists: extracting fields
  from one receipt is a different operation from detecting several
  receipts in one image.
- "split pdf" / "pdf splitting" / "split documents" claims are NOT
  in the phrase lists: splitting a generic PDF or document is a
  different operation from detecting receipts.
- "extract invoices" / "invoice extraction", "extract financial
  documents" / "financial document extraction", "extract bank
  statements" / "statement extraction", "extract tax forms" /
  "extract w2 forms", "extract pay stubs" / "payslip extraction",
  "extract us mail" / "us mail extraction", "extract contracts" /
  "contract extraction", "extract resumes" / "resume extraction",
  "extract bills of lading" / "bill of lading extraction",
  "extract delivery notes" / "delivery note extraction",
  "extract carte grises" / "carte grise extraction",
  "extract energy bills" / "energy bill extraction",
  "extract marriage certificates" / "marriage certificate
  extraction", "extract bank account details" / "bank details
  extraction", "extract nutrition facts labels" / "nutrition facts
  label extraction", "extract material certificates" / "material
  certificate extraction", and "extract bank checks" / "check
  extraction" claims are NOT in the phrase lists: this family
  covers multi-receipt detection only.
- As with every family: static pattern matching, not semantic
  judgement; dead code counts; alias chains the tracer cannot follow
  are missed; exact phrases only, not semantics; denial handling
  depends on the denial phrase list; each route must sit in a single
  module.

```
