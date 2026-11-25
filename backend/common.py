import json
import os
from decimal import Decimal
from datetime import datetime, timezone

import boto3
from botocore.config import Config

ddb = boto3.resource('dynamodb')
table = ddb.Table(os.environ['TABLE_NAME'])
region = os.environ.get('AWS_REGION') or os.environ.get('AWS_DEFAULT_REGION') or 'ap-southeast-2'
s3 = boto3.client('s3', region_name=region,
                  endpoint_url=f'https://s3.{region}.amazonaws.com',
                  config=Config(signature_version='s3v4'))
sns = boto3.client('sns')


def now():
    return datetime.now(timezone.utc).isoformat()


def response(status, body):
    return {
        'statusCode': status,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': os.environ.get('ALLOWED_ORIGIN', '*'),
            'Access-Control-Allow-Headers': 'Authorization,Content-Type',
            'Access-Control-Allow-Methods': 'GET,POST,DELETE,OPTIONS',
        },
        'body': json.dumps(body, default=lambda value: int(value) if isinstance(value, Decimal) and value % 1 == 0 else float(value)),
    }


def owner(event):
    return event['requestContext']['authorizer']['claims']['sub']


def get_file(user_id, file_id):
    return table.get_item(Key={'owner': user_id, 'fileId': file_id}).get('Item')


def update_file(item, status, **fields):
    if status in ('completed', 'failed'):
        fields['processingMs'] = max(0, int((datetime.now(timezone.utc) - datetime.fromisoformat(item['createdAt'])).total_seconds() * 1000))
    fields.update(status=status, updatedAt=now())
    names = {f'#f{i}': key for i, key in enumerate(fields)}
    values = {f':v{i}': value for i, value in enumerate(fields.values())}
    expression = 'SET ' + ', '.join(f'{key} = {value}' for key, value in zip(names, values))
    table.update_item(
        Key={'owner': item['owner'], 'fileId': item['fileId']},
        UpdateExpression=expression,
        ExpressionAttributeNames=names,
        ExpressionAttributeValues=values,
    )


def claim_file(item):
    table.update_item(
        Key={'owner': item['owner'], 'fileId': item['fileId']},
        UpdateExpression='SET #status = :processing, updatedAt = :updated',
        ConditionExpression='#status = :pending',
        ExpressionAttributeNames={'#status': 'status'},
        ExpressionAttributeValues={':pending': 'pending', ':processing': 'processing', ':updated': now()},
    )


def notify(item, status, detail=''):
    sns.publish(
        TopicArn=os.environ['NOTIFICATION_TOPIC_ARN'],
        Subject=f'CloudLens {status}: {item["name"]}'[:100],
        Message=json.dumps({'fileId': item['fileId'], 'owner': item['owner'], 'name': item['name'], 'status': status, 'detail': detail}),
    )
