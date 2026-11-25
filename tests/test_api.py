"""API contract tests with in-memory AWS stand-ins; no AWS account required."""
import importlib.util
import json
import os
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeKey:
    def __init__(self, name):
        self.name = name

    def eq(self, value):
        return self.name, value


class FakeTable:
    def __init__(self):
        self.items = {}

    def put_item(self, Item):
        self.items[(Item['owner'], Item['fileId'])] = Item

    def query(self, **kwargs):
        owner = kwargs['KeyConditionExpression'][1]
        return {'Items': [item for (user, _), item in self.items.items() if user == owner]}

    def delete_item(self, Key):
        self.items.pop((Key['owner'], Key['fileId']), None)


class FakeS3:
    def generate_presigned_url(self, action, Params, ExpiresIn):
        return f'https://signed.example/{action}/{Params["Key"]}'

    def delete_object(self, **_kwargs):
        pass


class ApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.table = FakeTable()
        cls.s3 = FakeS3()
        common = types.ModuleType('common')
        common.table = cls.table
        common.s3 = cls.s3
        common.owner = lambda event: event['user']
        common.get_file = lambda user, file_id: cls.table.items.get((user, file_id))
        common.now = lambda: '2026-01-01T00:00:00+00:00'
        common.response = lambda status, body: {'statusCode': status, 'body': json.dumps(body)}
        boto3 = types.ModuleType('boto3')
        dynamodb = types.ModuleType('boto3.dynamodb')
        conditions = types.ModuleType('boto3.dynamodb.conditions')
        conditions.Key = FakeKey
        modules = {'common': common, 'boto3': boto3, 'boto3.dynamodb': dynamodb,
                   'boto3.dynamodb.conditions': conditions}
        cls.module_patch = patch.dict(sys.modules, modules)
        cls.module_patch.start()
        cls.env_patch = patch.dict(os.environ, {'RAW_BUCKET': 'raw', 'PROCESSED_BUCKET': 'processed'})
        cls.env_patch.start()
        spec = importlib.util.spec_from_file_location('cloudlens_api', Path(__file__).parents[1] / 'backend' / 'api.py')
        cls.api = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.api)

    @classmethod
    def tearDownClass(cls):
        cls.env_patch.stop()
        cls.module_patch.stop()

    def setUp(self):
        self.table.items.clear()

    def event(self, method, path, user='alice', body=None, file_id=None):
        return {'httpMethod': method, 'path': path, 'user': user,
                'body': json.dumps(body) if body is not None else None,
                'pathParameters': {'fileId': file_id} if file_id else None}

    def test_upload_rejects_oversize_and_unsupported_type(self):
        for content_type, size in [('image/jpeg', 11 * 1024 * 1024), ('text/plain', 100)]:
            reply = self.api.handler(self.event('POST', '/upload-url', body={
                'name': 'test.txt', 'contentType': content_type, 'size': size,
            }), None)
            self.assertEqual(reply['statusCode'], 400)
        self.assertFalse(self.table.items)

    def test_upload_creates_owner_scoped_record(self):
        reply = self.api.handler(self.event('POST', '/upload-url', body={
            'name': 'photo.jpg', 'contentType': 'image/jpeg', 'size': 1200,
        }), None)
        self.assertEqual(reply['statusCode'], 201)
        file_id = json.loads(reply['body'])['file']['fileId']
        self.assertEqual(self.table.items[('alice', file_id)]['status'], 'pending')
        forbidden = self.api.handler(self.event('GET', f'/files/{file_id}', user='bob', file_id=file_id), None)
        self.assertEqual(forbidden['statusCode'], 404)

    def test_download_requires_completed_status(self):
        item = {'owner': 'alice', 'fileId': 'id', 'status': 'processing', 'processedKey': 'alice/id/image.webp'}
        self.table.items[('alice', 'id')] = item
        event = self.event('GET', '/files/id/download', file_id='id')
        self.assertEqual(self.api.handler(event, None)['statusCode'], 409)
        item['status'] = 'completed'
        self.assertEqual(self.api.handler(event, None)['statusCode'], 200)


if __name__ == '__main__':
    unittest.main()
