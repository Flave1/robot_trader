
import json
import boto3
from datetime import datetime

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('FileMetadata') 

def lambda_handler(event, context):
    for record in event['Records']:
        s3_info = record['s3']
        bucket = s3_info['bucket']['name']
        key = s3_info['object']['key']
        size = s3_info['object'].get('size', 0)

        metadata = {
            'FileName': key,
            'Bucket': bucket,
            'Size': size,
            'UploadedAt': datetime.utcnow().isoformat()
        }

        table.put_item(Item=metadata)

    return {
        'statusCode': 200,
        'body': json.dumps('Metadata saved to DynamoDB')
    }
