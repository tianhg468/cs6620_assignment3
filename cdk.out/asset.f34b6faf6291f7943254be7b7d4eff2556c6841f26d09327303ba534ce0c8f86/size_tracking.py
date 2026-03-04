import os
import boto3
from datetime import datetime, timezone

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]


def handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    # Compute total size and object count
    paginator = s3.get_paginator("list_objects_v2")
    total_size = 0
    total_count = 0
    for page in paginator.paginate(Bucket=BUCKET_NAME):
        for obj in page.get("Contents", []):
            total_size += obj["Size"]
            total_count += 1

    now = datetime.now(timezone.utc).isoformat()

    table.put_item(Item={
        "bucket_name": BUCKET_NAME,
        "timestamp": now,
        "total_size": total_size,
        "total_count": total_count,
    })

    print(f"Recorded size={total_size}, count={total_count} at {now}")
    return {"statusCode": 200}