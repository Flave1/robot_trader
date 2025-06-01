import boto3
from botocore.exceptions import ClientError

dynamodb = boto3.resource('dynamodb')
table_name = 'FileMetadata' 
table = dynamodb.Table(table_name)

def put_item(item):
    """
    Insert or update an item in DynamoDB.
    """
    try:
        table.put_item(Item=item)
        print(f"Item added: {item}")
    except ClientError as e:
        print(f"Failed to put item: {e.response['Error']['Message']}")

def get_item(key):
    """
    Retrieve an item by primary key.
    `key` should be a dictionary like: {'FileName': 'example.txt'}
    """
    try:
        response = table.get_item(Key=key)
        return response.get('Item')
    except ClientError as e:
        print(f"Failed to get item: {e.response['Error']['Message']}")
        return None

def update_item(key, attribute_updates):
    """
    Update attributes of an item.
    `attribute_updates` is a dict like: {'Size': 2048}
    """
    try:
        update_expression = "SET " + ", ".join(f"{k} = :{k}" for k in attribute_updates)
        expression_values = {f":{k}": v for k, v in attribute_updates.items()}
        table.update_item(
            Key=key,
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_values
        )
        print(f"Item updated: {key}")
    except ClientError as e:
        print(f"Failed to update item: {e.response['Error']['Message']}")

def delete_item(key):
    """
    Delete an item by key.
    """
    try:
        table.delete_item(Key=key)
        print(f"Item deleted: {key}")
    except ClientError as e:
        print(f"Failed to delete item: {e.response['Error']['Message']}")
