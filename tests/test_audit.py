"""Regression suite: fixtures are parsed as text, never imported or executed."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from multi_receipts_detection_claim_audit.audit import audit, document_claims, module_evidence, normalize
from multi_receipts_detection_claim_audit.__main__ import main
from multi_receipts_detection_claim_audit.phrases import GENERIC_NAMES, MULTIRECEIPTSDETECTION, NOMULTIRECEIPTSDETECTION

EXPECTED_POSITIVE = ('multi receipt detection', 'detect multi receipts', 'detects multi receipts', 'detecting multi receipts', 'multi receipts detector', 'multi receipt detector', 'multi receipts detection', 'detect multiple receipts', 'detects multiple receipts', 'detecting multiple receipts', 'multiple receipt detection', 'multiple receipts detection', 'multiple receipts detector', 'multiple receipt detector', 'detect receipts in one image', 'detects receipts in one image', 'detecting receipts in one image', 'detect receipts in a single image', 'detects receipts in a single image', 'detecting receipts in a single image', 'receipt detection', 'detect receipts', 'detects receipts', 'detecting receipts', 'receipts detector', 'receipt detector', 'locate receipts', 'locates receipts', 'locating receipts', 'find receipts in one image', 'finds receipts in one image', 'finding receipts in one image', 'count receipts', 'counts receipts', 'counting receipts', 'receipt counting', 'count receipts in one image', 'counts receipts in one image', 'counting receipts in one image', 'detect receipt positions', 'detects receipt positions', 'detecting receipt positions', 'receipt positions', 'locate receipt positions', 'locates receipt positions', 'locating receipt positions', 'receipt bounding boxes', 'receipts bounding box', 'detect receipt bounding boxes', 'multi receipt locator')
EXPECTED_NEGATIVE = ('no multi receipt detection', 'does not detect multi receipts', 'does not support multi receipt detection', 'without multi receipt detection', 'no multi receipts detector', 'does not detect multiple receipts', 'no multiple receipt detection', 'does not detect receipts', 'no receipt detection', 'receipt detection not supported', 'does not detect receipts in one image', 'no receipts detector', 'does not locate receipts', 'no receipt detector', 'does not count receipts', 'no receipt counting', 'does not find receipts', 'without receipt detection', 'no multi receipt detector', 'does not detect receipt positions', 'no receipt positions detection', 'does not support receipt detection', 'without multi receipts detection', 'no multiple receipts detector')
EXPECTED_GENERIC = ('detect_multi_receipts', 'detect_multi_receipt', 'multi_receipts_detector', 'multi_receipt_detector', 'multi_receipts_detection', 'detect_multiple_receipts', 'detect_receipts_in_image', 'detect_receipts', 'detect_receipt', 'receipt_detector', 'receipts_detector', 'locate_receipts', 'locate_receipt', 'find_receipts', 'find_receipt', 'count_receipts', 'count_receipt', 'receipt_position_detection', 'detect_receipt_positions', 'extract_receipt_positions', 'multi_receipt_detection', 'receipts_in_image_detection', 'find_receipts_in_image', 'locate_receipts_in_image')

PAIR = 'from mindee import Client\nc = Client()\nc.parse(MultiReceiptsDetectorV1, source)\n'
OTHER_PRODUCTS = '''ReceiptV5 InvoiceV4 InvoiceSplitterV1 FinancialDocumentV1 PassportV1 BankCheckV1 BankAccountDetailsV1 BankAccountDetailsV2 PayslipV2 PayslipV3 NutritionFactsLabelV1 HealthcareCardV1 BusinessCardV1 CustomV1 GeneratedV1 BillOfLadingV1 ResumeV1 DeliveryNoteV1 DriverLicenseV1 IdCardV1 InternationalIdV2 CarteGriseV1 EnergyBillV1 MaterialCertificateV1 BarcodeReaderV1 CropperV1 UsMailV2 UsMailV3 MultiReceiptsDetectorV2 TypeMultiReceiptsDetectorV1'''.split()
NOT_CALLS = '''extract_receipts begin_analyze_document process_document process_document_url process_any_document process_any_document_url split_and_process_pdf split_and_process_pdf_url process_multi_receipts process_multi_receipts_url detect_multi_receipts_document process_w2_document process_w9_document process_w8_document split_and_process_w2 split_and_process_w2_url process_check process_check_url process_check_with_remittance process_check_with_remittance_url process_bank_statement_document process_bank_statement_document_url process_bussines_card_document process_bussines_card_document_url classify_document get_business_cards get_business_card delete_business_card get_pdf get_documents_from_pdf batch_process_documents analyze_document analyze_expense analyze_id start_document_analysis get_expense_analysis extract extract_text image_to_string read_csv read_excel read_pdf convert_into extract_table extract_tables find_table find_tables findContours boundingRect YOLO is_receipt detect_document detect_objects document_detector object_detector search findall parse_string upload parse load_data'''.split()


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def write(self, path, text):
        file = self.root / path
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(text, encoding='utf-8')
        return file

    def evidence(self, code):
        return module_evidence(code, 'app.py')

    def cli(self, *args):
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                status = main(list(args))
            except SystemExit as error:
                status = error.code
        return status, stdout.getvalue(), stderr.getvalue()

    def test_exact_vocabulary(self):
        self.assertEqual(MULTIRECEIPTSDETECTION, EXPECTED_POSITIVE)
        self.assertEqual(NOMULTIRECEIPTSDETECTION, EXPECTED_NEGATIVE)
        self.assertEqual(GENERIC_NAMES, EXPECTED_GENERIC)
        self.assertEqual(tuple(map(len, (set(EXPECTED_POSITIVE), set(EXPECTED_NEGATIVE), set(EXPECTED_GENERIC)))), (50, 24, 24))

    def test_normalization(self):
        self.assertEqual(normalize("DOESN'T\n detect multi-receipts"), 'does not detect multi receipts')
        claims = document_claims("Doesn't detect multi-receipts", 'README.md')
        self.assertEqual([x['family'] for x in claims], ['NOMULTIRECEIPTSDETECTION'])

    def test_boundaries(self):
        self.assertEqual(document_claims('xreceipt detectionx', 'README.md'), [])

    def test_longest_and_tie(self):
        claims = document_claims('detect receipts in a single image and detect receipts', 'README.md')
        self.assertEqual([x['phrase'] for x in claims], ['detect receipts in a single image', 'detect receipts'])

    def test_paragraphs_and_inline(self):
        claims = document_claims('Heading\n\nWe `detect receipts`\nin one image.\n\nNo receipt detection', 'README.md')
        self.assertEqual([x['line'] for x in claims], [3, 6])
        self.assertEqual([x['family'] for x in claims], ['MULTIRECEIPTSDETECTION', 'NOMULTIRECEIPTSDETECTION'])

    def test_multiple_denials_removed(self):
        claims = document_claims('does not detect multi receipts; no receipt detection; detect receipts', 'README.md')
        self.assertEqual([x['family'] for x in claims].count('MULTIRECEIPTSDETECTION'), 1)

    def test_four_space_fence_is_prose(self):
        self.assertTrue(document_claims('    ```\nreceipt detection\n    ```', 'README.md'))

    def test_unclosed_fence(self):
        self.assertEqual(document_claims('~~~\nreceipt detection', 'README.md'), [])

    def test_wrong_fence_cannot_close(self):
        self.assertEqual(document_claims('````\n```\nreceipt detection\n~~~~\nreceipt detection', 'README.md'), [])

    def test_mindee_alias(self):
        self.assertTrue(self.evidence('from mindee import Client as C\nc=C()\nc.parse(product.MultiReceiptsDetectorV1, source)'))

    def test_mindee_direct(self):
        self.assertTrue(self.evidence('import mindee\nc=mindee.Client()\nx.parse(source, product_class=mindee.product.MultiReceiptsDetectorV1)'))

    def test_mindee_v5(self):
        self.assertTrue(self.evidence('from mindee import Client\nfrom mindee.v1.product import MultiReceiptsDetectorV1\nc=Client()\nc.parse(MultiReceiptsDetectorV1, source)'))

    def test_mindee_alias_module_is_outside_exact_client_form(self):
        self.assertEqual(self.evidence('import mindee as m\nc=m.Client()\nc.parse(MultiReceiptsDetectorV1, source)'), [])

    def test_split_modules(self):
        self.write('README.md', 'receipt detection')
        self.write('one.py', 'from mindee import Client\nc=Client()')
        self.write('two.py', 'import mindee\nc.parse(MultiReceiptsDetectorV1, source)')
        self.assertEqual(audit(self.root)['findings'][0]['severity'], 'HIGH')

    def test_import_gate(self):
        self.assertEqual(self.evidence('c=mindee.Client()\nc.parse(MultiReceiptsDetectorV1, source)'), [])

    def test_lone_parts(self):
        for text in ('import mindee', 'from mindee import Client\nc=Client()', 'import mindee\nc.parse(MultiReceiptsDetectorV1, x)'):
            with self.subTest(text=text):
                self.assertEqual(self.evidence(text), [])

    def test_invalid_syntax(self):
        self.assertEqual(self.evidence('x.detect_receipts(\n'), [])

    def test_comments_strings_references(self):
        self.assertEqual(self.evidence('# x.detect_receipts()\ns="x.detect_receipts()"\nx.detect_receipts'), [])

    def test_dead_code_counts(self):
        self.assertTrue(self.evidence('if False:\n    x.detect_receipts()'))

    def test_subprocess(self):
        self.assertEqual(self.evidence('import subprocess\nsubprocess.run(["mindee", "detect_receipts"])'), [])

    def test_eden_and_raw_http(self):
        for url in ('https://api.edenai.run/v2/universal-ai', 'https://api.veryfi.com/api/v8/partner/documents', 'https://app.nanonets.com/api/v2/OCR/Model/opaque/LabelFile/'):
            self.assertEqual(self.evidence('import requests\nrequests.post(' + repr(url) + ', json={"model":"multi_receipts_detector"})'), [])

    def test_ocr_regex_csv_pdf_shapes(self):
        self.assertEqual(self.evidence('import re\ntext=p.extract_text()\nre.findall("receipt", text)\nboxes=[(0,0,1,1)]\nfor page in reader.pages:\n writer.add_page(page)\ncv2.findContours(image, mode, method)\npandas.read_csv(path)'), [])

    def test_positive_without_source(self):
        self.write('README.md', 'receipt detection')
        result = audit(self.root)
        self.assertEqual(result['source_files'], 0)
        self.assertEqual(result['findings'][0]['rule'], 'documented-multi-receipts-detection-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')

    def test_denial_without_source(self):
        self.write('README.md', 'no receipt detection')
        self.assertEqual(audit(self.root)['verdict'], 'PASS')

    def test_denial_with_production(self):
        self.write('README.md', 'no receipt detection')
        self.write('app.py', PAIR)
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['rule'], 'documented-no-multi-receipts-detection-claim-false')
        self.assertEqual(result['findings'][0]['severity'], 'HIGH')

    def test_one_finding_per_family(self):
        self.write('README.md', 'receipt detection\n\ndetect receipts\n\ncount receipts')
        self.assertEqual(len(audit(self.root)['findings']), 1)

    def test_both_claims(self):
        self.write('README.md', 'receipt detection\n\nno receipt detection')
        self.write('app.py', PAIR)
        self.assertEqual([x['rule'] for x in audit(self.root)['findings']], ['documented-no-multi-receipts-detection-claim-false'])

    def test_docs_selection(self):
        self.write('other.md', 'receipt detection')
        self.write('sub/README.md', 'receipt detection')
        self.assertEqual(audit(self.root)['claims'], [])
        self.write('nested/docs/deep/claims.md', 'receipt detection')
        self.assertEqual(len(audit(self.root)['claims']), 1)

    def test_ignore_prefix_component(self):
        self.write('README.md', 'receipt detection')
        self.write('vendor/app.py', PAIR)
        self.write('vendorish/app.py', PAIR)
        self.assertEqual(len(audit(self.root, ['vendor'])['evidence']), 1)
        self.assertEqual(audit(self.root, ['vendor', 'vendorish'])['findings'][0]['severity'], 'HIGH')

    def test_symlinks(self):
        self.write('README.md', 'receipt detection')
        outside = Path(self.tmp.name + '-outside')
        outside.mkdir()
        self.addCleanup(lambda: __import__('shutil').rmtree(outside))
        (outside / 'app.py').write_text(PAIR)
        (self.root / 'link.py').symlink_to(outside / 'app.py')
        (self.root / 'linked').symlink_to(outside, target_is_directory=True)
        self.assertEqual(audit(self.root)['evidence'], [])

    def test_cli_json_high(self):
        self.write('README.md', 'receipt detection')
        code, output, _ = self.cli('audit', str(self.root), '--json')
        self.assertEqual(code, 2)
        self.assertEqual(json.loads(output)['findings'][0]['severity'], 'HIGH')

    def test_cli_test_thresholds(self):
        self.write('README.md', 'receipt detection')
        self.write('tests/test_app.py', PAIR)
        self.assertEqual(self.cli('audit', str(self.root))[0], 0)
        self.assertEqual(self.cli('audit', str(self.root), '--fail-on', 'medium')[0], 2)

    def test_cli_pass_verbose_default_repo(self):
        self.write('README.md', 'receipt detection')
        self.write('app.py', PAIR)
        import os
        previous = os.getcwd()
        try:
            os.chdir(self.root)
            code, output, _ = self.cli('audit', '--verbose')
        finally:
            os.chdir(previous)
        self.assertEqual(code, 0)
        self.assertIn('app.py:3', output)

    def test_cli_ignore_repeatable(self):
        self.write('docs/a.md', 'receipt detection')
        self.write('other/docs/b.md', 'receipt detection')
        self.assertEqual(self.cli('audit', str(self.root), '--ignore', 'docs', '--ignore', 'other')[0], 0)

    def test_cli_usage_errors(self):
        for args in ((), ('nope',), ('audit', '--fail-on', 'HIGH'), ('audit', '--ignore'), ('audit', '.', '--ignore', 'a', 'b'), ('audit', '--bogus')):
            with self.subTest(args=args):
                self.assertEqual(self.cli(*args)[0], 1)

    def test_cli_bad_path(self):
        self.assertEqual(self.cli('audit', str(self.root / 'absent'))[0], 1)
        self.write('file', '')
        self.assertEqual(self.cli('audit', str(self.root / 'file'))[0], 1)

    def test_cli_io_error(self):
        with patch('multi_receipts_detection_claim_audit.__main__.audit', side_effect=PermissionError('unreadable')):
            self.assertEqual(self.cli('audit', str(self.root))[0], 1)

    def test_cli_invalid_encoding(self):
        (self.root / 'README.md').write_bytes(b'\xff')
        self.assertEqual(self.cli('audit', str(self.root))[0], 1)

    def test_cli_version(self):
        code, output, _ = self.cli('--version')
        self.assertEqual((code, output.strip()), (0, '0.1.0'))

    def test_readme_self_audit(self):
        repo = Path(__file__).resolve().parents[1]
        self.assertEqual(document_claims((repo / 'README.md').read_text(), 'README.md'), [])

    def test_no_execution(self):
        self.write('app.py', 'raise RuntimeError("must never execute")\nx.detect_receipts()')
        self.assertTrue(audit(self.root)['evidence'])


def add_case(name, callback):
    callback.__name__ = 'test_' + name
    setattr(AuditTests, callback.__name__, callback)


def phrase_case(phrase, family):
    def test(self):
        claims = document_claims(phrase, 'README.md')
        self.assertEqual([(x['family'], x['phrase']) for x in claims], [(family, phrase)])
    return test


for index, phrase in enumerate(EXPECTED_POSITIVE):
    add_case('positive_phrase_%02d' % index, phrase_case(phrase, 'MULTIRECEIPTSDETECTION'))
for index, phrase in enumerate(EXPECTED_NEGATIVE):
    add_case('negative_phrase_%02d' % index, phrase_case(phrase, 'NOMULTIRECEIPTSDETECTION'))


def generic_case(name, form):
    def test(self):
        code = {'attribute': 'obj.' + name + '(image)',
                'import': 'from detector import ' + name + '\n' + name + '(image)',
                'alias': 'from detector import ' + name + ' as run\nrun(image)',
                'bare': name + '(image)',
                'import_only': 'from detector import ' + name}[form]
        self.assertEqual(bool(self.evidence(code)), form in ('attribute', 'import', 'alias'))
    return test


for name in EXPECTED_GENERIC:
    for form in ('attribute', 'import', 'alias', 'bare', 'import_only'):
        add_case('generic_' + name + '_' + form, generic_case(name, form))


def other_product_case(product):
    def test(self):
        self.assertEqual(self.evidence(PAIR.replace('MultiReceiptsDetectorV1', product)), [])
    return test


for product in OTHER_PRODUCTS:
    add_case('not_product_' + product, other_product_case(product))


def not_call_case(name):
    def test(self):
        imports = 'import mindee, veryfi, boto3, requests, cv2, ultralytics\nimport azure.ai.documentintelligence\nimport google.cloud.documentai\n'
        self.assertEqual(self.evidence(imports + 'client.' + name + '("prebuilt-receipt")'), [])
    return test


for name in NOT_CALLS:
    add_case('not_call_' + name, not_call_case(name))


def fence_case(marker, indent):
    def test(self):
        fence = ' ' * indent + marker
        self.assertEqual(document_claims(fence + 'text\nreceipt detection\n' + fence + '\n', 'README.md'), [])
    return test


for marker in ('```', '~~~~'):
    for indent in range(4):
        add_case('fence_' + str(len(marker)) + '_' + str(indent), fence_case(marker, indent))


def path_case(path, expected):
    def test(self):
        self.write('README.md', 'receipt detection')
        self.write(path, PAIR)
        result = audit(self.root)
        self.assertEqual(result['findings'][0]['severity'] if result['findings'] else 'PASS', expected)
    return test


for index, (path, expected) in enumerate((('tests/a.py', 'MEDIUM'), ('test_app.py', 'MEDIUM'), ('app_test.py', 'MEDIUM'), ('nested/tests/a.py', 'MEDIUM'), ('fixtures/a.py', 'HIGH'), ('docs/a.py', 'HIGH'), ('examples/a.py', 'HIGH'), ('nested/examples/a.py', 'HIGH'), ('app.py', 'PASS'))):
    add_case('source_path_%02d' % index, path_case(path, expected))


def shadow_case(binding, target):
    def test(self):
        code = {'generic': 'from vendor import detect_receipts as run\nrun(x)',
                'client': PAIR,
                'module': 'import mindee\nc=mindee.Client()\nc.parse(MultiReceiptsDetectorV1, x)',
                'product': PAIR}[target]
        self.assertEqual(self.evidence(code + '\n' + binding), [])
    return test


for target, name in (('generic', 'run'), ('client', 'Client'), ('module', 'mindee'), ('product', 'MultiReceiptsDetectorV1')):
    for index, binding in enumerate(('def {n}(): pass', 'class {n}: pass', '{n} = other', '{n}: object = other', 'with other() as {n}: pass', 'async def f():\n async with other() as {n}: pass', 'class C:\n def {n}(self): pass', '({n}, other) = values')):
        add_case('shadow_' + target + '_' + str(index), shadow_case(binding.format(n=name), target))


def product_form_case(product, keyword):
    def test(self):
        code = 'import mindee\nc=mindee.Client()\nc.parse(' + ('product_class=' if keyword else '') + product + ')'
        self.assertTrue(self.evidence(code))
    return test


for index, product in enumerate(('MultiReceiptsDetectorV1', 'product.MultiReceiptsDetectorV1', 'mindee.product.MultiReceiptsDetectorV1', 'mindee.product.multi_receipts_detector.MultiReceiptsDetectorV1')):
    for keyword in (False, True):
        add_case('product_form_' + str(index) + '_' + str(keyword), product_form_case(product, keyword))


def attribute_shadow_case(name, binding):
    def test(self):
        self.assertEqual(self.evidence('obj.' + name + '(image)\n' + binding.format(n=name)), [])
    return test


for name in EXPECTED_GENERIC:
    for index, binding in enumerate(('def {n}(): pass', 'class C:\n def {n}(self): pass', '{n} = replacement', '{n}: object = replacement', 'with manager() as {n}: pass', 'async def f():\n async with manager() as {n}: pass')):
        add_case('attribute_shadow_' + name + '_' + str(index), attribute_shadow_case(name, binding))


if __name__ == '__main__':
    unittest.main()
