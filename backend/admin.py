from common import response, table


def handler(event, _context):
    groups = event['requestContext']['authorizer']['claims'].get('cognito:groups', '')
    if 'admins' not in {group.strip() for group in groups.strip('[]').split(',')}:
        return response(403, {'error': 'Admin access required.'})
    counts = {'pending': 0, 'processing': 0, 'completed': 0, 'failed': 0}
    total_bytes = 0
    saved_bytes = 0
    latency_sum = 0
    latency_count = 0
    cursor = None
    while True:
        args = {'ProjectionExpression': '#s, #z, processedSize, processingMs',
                'ExpressionAttributeNames': {'#s': 'status', '#z': 'size'}}
        if cursor:
            args['ExclusiveStartKey'] = cursor
        page = table.scan(**args)
        for item in page['Items']:
            counts[item['status']] = counts.get(item['status'], 0) + 1
            if item['status'] == 'completed':
                total_bytes += int(item.get('size', 0))
                saved_bytes += max(0, int(item.get('size', 0)) - int(item.get('processedSize', 0)))
                if 'processingMs' in item:
                    latency_sum += int(item['processingMs'])
                    latency_count += 1
        cursor = page.get('LastEvaluatedKey')
        if not cursor:
            break
    total = sum(counts.values())
    terminal = counts['completed'] + counts['failed']
    return response(200, {'counts': counts, 'totalOriginalBytes': total_bytes, 'bytesSaved': saved_bytes,
                          'failureRate': round(counts['failed'] / terminal * 100, 1) if terminal else 0,
                          'averageLatencyMs': round(latency_sum / latency_count) if latency_count else 0,
                          'totalFiles': total})
