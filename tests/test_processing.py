"""Exercise the image and OCR paths without making AWS calls."""
import importlib.util
import io
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageDraw


BACKEND = Path(__file__).parents[1] / 'backend'
SAMPLE = Path(__file__).parents[1] / 'public' / 'sample-photo.jpg'
SAMPLE_PDF = Path(__file__).parents[1] / 'public' / 'sample-invoice.pdf'


def load_module(name, filename):
    spec = importlib.util.spec_from_file_location(name, BACKEND / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeS3:
    def __init__(self):
        self.objects = {}

    def get_object(self, Bucket, Key):
        return {'Body': io.BytesIO(self.objects[(Bucket, Key)])}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body
        self.last_content_type = ContentType


class ProcessingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.s3 = FakeS3()
        cls.updates = []
        cls.notifications = []
        common = types.ModuleType('common')
        common.s3 = cls.s3
        common.update_file = lambda item, status, **fields: cls.updates.append((status, fields))
        common.notify = lambda item, status, detail='': cls.notifications.append(status)
        common.claim_file = lambda item: None
        common.get_file = lambda owner, file_id: None
        botocore = types.ModuleType('botocore')
        exceptions = types.ModuleType('botocore.exceptions')
        exceptions.ClientError = type('ClientError', (Exception,), {})
        cls.modules = patch.dict(sys.modules, {'common': common, 'botocore': botocore,
                                                'botocore.exceptions': exceptions})
        cls.modules.start()
        cls.environment = patch.dict(os.environ, {'RAW_BUCKET': 'raw', 'PROCESSED_BUCKET': 'processed'})
        cls.environment.start()
        cls.processor = load_module('cloudlens_process_test', 'process.py')

    @classmethod
    def tearDownClass(cls):
        cls.environment.stop()
        cls.modules.stop()

    def setUp(self):
        self.s3.objects.clear()
        self.updates.clear()
        self.notifications.clear()

    def test_image_becomes_webp(self):
        item = {'owner': 'alice', 'fileId': 'image-id', 'name': 'sample-photo.jpg',
                'rawKey': 'alice/image-id/sample-photo.jpg'}
        self.s3.objects[('raw', item['rawKey'])] = SAMPLE.read_bytes()
        self.processor.process_image(item)
        result = self.s3.objects[('processed', 'alice/image-id/image.webp')]
        with Image.open(io.BytesIO(result)) as image:
            self.assertEqual(image.format, 'WEBP')
            self.assertLessEqual(max(image.size), 1920)
        self.assertEqual(self.s3.last_content_type, 'image/webp')
        self.assertEqual(self.updates[-1][0], 'completed')
        self.assertEqual(self.updates[-1][1]['processedSize'], len(result))
        self.assertEqual(self.notifications, ['completed'])

    def test_invalid_image_is_rejected(self):
        item = {'owner': 'alice', 'fileId': 'image-id', 'rawKey': 'bad'}
        self.s3.objects[('raw', 'bad')] = b'not a real image'
        with self.assertRaisesRegex(ValueError, 'damaged or unsupported'):
            self.processor.process_image(item)
        self.assertFalse(self.updates)

    def test_pdf_extracts_embedded_text(self):
        item = {'owner': 'alice', 'fileId': 'pdf-id', 'name': 'invoice.pdf', 'rawKey': 'alice/pdf-id/invoice.pdf'}
        self.s3.objects[('raw', item['rawKey'])] = SAMPLE_PDF.read_bytes()
        self.processor.process_pdf(item)
        result = self.s3.objects[('processed', 'alice/pdf-id/extracted.txt')]
        self.assertIn(b'SAMPLE INVOICE', result)
        self.assertEqual(self.updates[-1][0], 'completed')
        self.assertEqual(self.notifications, ['completed'])

    def test_scanned_pdf_sends_rendered_page_to_ocr(self):
        image = Image.new('RGB', (700, 120), 'white')
        ImageDraw.Draw(image).text((30, 40), 'Scanned invoice', fill='black')
        buffer = io.BytesIO()
        image.save(buffer, format='PDF')
        item = {'owner': 'alice', 'fileId': 'scan-id', 'name': 'scan.pdf', 'rawKey': 'alice/scan-id/scan.pdf'}
        self.s3.objects[('raw', item['rawKey'])] = buffer.getvalue()
        def fake_ocr(args, **kwargs):
            self.assertEqual(args[1:3], ['stdin', 'stdout'])
            self.assertTrue(kwargs['input'].startswith(b'\x89PNG'))
            return types.SimpleNamespace(stdout=b'Scanned invoice\n')
        with patch.object(self.processor.subprocess, 'run', side_effect=fake_ocr):
            self.processor.process_pdf(item)
        self.assertEqual(self.s3.objects[('processed', 'alice/scan-id/extracted.txt')], b'Scanned invoice')
        self.assertEqual(self.notifications, ['completed'])


if __name__ == '__main__':
    unittest.main()
