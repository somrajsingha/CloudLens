import json
import os
import uuid
from datetime import datetime, timezone
from urllib.parse import quote

from boto3.dynamodb.conditions import Key

from common import get_file, now, owner, response, s3, table

RAW = os.environ['RAW_BUCKET']
PROCESSED = os.environ['PROCESSED_BUCKET']
MAX_SIZE = 10 * 1024 * 1024
TYPES = {'image/jpeg': 'image', 'image/png': 'image', 'application/pdf': 'pdf'}


def public_item(item):
    return {key: item.get(key) for key in (
        'fileId', 'name', 'type', 'contentType', 'size', 'processedSize',
        'status', 'createdAt', 'updatedAt', 'error', 'extractedText',
    ) if key in item}


def handler(event, _context):
    try:
        return route(event)
    except (ValueError, KeyError, json.JSONDecodeError) as exc:
        return response(400, {'error': str(exc)})
    except Exception:
        import logging
        logging.exception('API request failed')
        return response(500, {'error': 'The request could not be completed.'})


def route(event):
    method = event['httpMethod']
    path = event['path']
    user_id = owner(event)
    params = event.get('pathParameters') or {}
    file_id = params.get('fileId')

    if method == 'POST' and path == '/upload-url':
        body = json.loads(event.get('body') or '{}')
        name = str(body.get('name', '')).strip()
        content_type = body.get('contentType')
        size = body.get('size')
        if not name or len(name) > 255 or '/' in name or '\\' in name:
            raise ValueError('Choose a valid file name of at most 255 characters.')
        if content_type not in TYPES or not isinstance(size, int) or not 0 < size <= MAX_SIZE:
            raise ValueError('Only JPG, PNG, or PDF files up to 10 MB are accepted.')
        file_id = str(uuid.uuid4())
        key = f'{user_id}/{file_id}/{quote(name, safe="")}'
        item = {'owner': user_id, 'fileId': file_id, 'name': name, 'type': TYPES[content_type],
                'contentType': content_type, 'size': size, 'rawKey': key,
                'status': 'pending', 'createdAt': now(), 'updatedAt': now()}
        table.put_item(Item=item)
        url = s3.generate_presigned_url('put_object', Params={
            'Bucket': RAW, 'Key': key, 'ContentType': content_type,
        }, ExpiresIn=900)
        return response(201, {'file': public_item(item), 'uploadUrl': url, 'headers': {'Content-Type': content_type}})

    if method == 'GET' and path == '/files':
        items = []
        cursor = None
        while True:
            args = {'KeyConditionExpression': Key('owner').eq(user_id)}
            if cursor:
                args['ExclusiveStartKey'] = cursor
            page = table.query(**args)
            items.extend(page['Items'])
            cursor = page.get('LastEvaluatedKey')
            if not cursor:
                break
        items.sort(key=lambda item: item['createdAt'], reverse=True)
        return response(200, {'files': [public_item(item) for item in items]})

    if file_id:
        item = get_file(user_id, file_id)
        if not item:
            return response(404, {'error': 'File not found.'})
        if method == 'GET' and path.endswith('/download'):
            if item['status'] != 'completed' or 'processedKey' not in item:
                return response(409, {'error': 'This file is not ready yet.'})
            url = s3.generate_presigned_url('get_object', Params={
                'Bucket': PROCESSED, 'Key': item['processedKey'],
                'ResponseContentDisposition': f'attachment; filename="{item["fileId"]}{os.path.splitext(item["processedKey"])[1]}"',
            }, ExpiresIn=300)
            return response(200, {'downloadUrl': url})
        if method == 'GET':
            return response(200, {'file': public_item(item)})
        if method == 'DELETE':
            s3.delete_object(Bucket=RAW, Key=item['rawKey'])
            if item.get('processedKey'):
                s3.delete_object(Bucket=PROCESSED, Key=item['processedKey'])
            table.delete_item(Key={'owner': user_id, 'fileId': file_id})
            return response(200, {'deleted': True})

    return response(404, {'error': 'Route not found.'})
