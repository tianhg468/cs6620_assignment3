import os
import io
import boto3
import json
from datetime import datetime, timezone, timedelta
from boto3.dynamodb.conditions import Key

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

TABLE_NAME = os.environ["TABLE_NAME"]
BUCKET_NAME = os.environ["BUCKET_NAME"]
SIZE_INDEX_NAME = os.environ["SIZE_INDEX_NAME"]


def handler(event, context):
    table = dynamodb.Table(TABLE_NAME)

    now = datetime.now(timezone.utc)
    ten_seconds_ago = (now - timedelta(seconds=10)).isoformat()
    now_iso = now.isoformat()

    # Query items for TestBucket in the last 10 seconds (using primary key)
    response = table.query(
        KeyConditionExpression=Key("bucket_name").eq(BUCKET_NAME)
        & Key("timestamp").between(ten_seconds_ago, now_iso)
    )
    items = response.get("Items", [])

    # Find the maximum size ANY bucket has ever reached using the GSI
    max_size = 0

    # Query size-index for TestBucket (descending by total_size, limit 1)
    max_resp = table.query(
        IndexName=SIZE_INDEX_NAME,
        KeyConditionExpression=Key("bucket_name").eq(BUCKET_NAME),
        ScanIndexForward=False,
        Limit=1,
    )
    if max_resp.get("Items"):
        max_size = max(max_size, int(max_resp["Items"][0]["total_size"]))

    # To support any bucket, you'd iterate known bucket names similarly.

    # Build plot
    timestamps = []
    sizes = []
    for item in sorted(items, key=lambda x: x["timestamp"]):
        ts = datetime.fromisoformat(item["timestamp"])
        timestamps.append(ts)
        sizes.append(int(item["total_size"]))

    fig, ax = plt.subplots(figsize=(10, 6))

    if timestamps:
        ax.plot(timestamps, sizes, marker="o", label="Bucket size (bytes)")
        ax.axhline(y=max_size, color="r", linestyle="--", label=f"Max ever = {max_size} B")
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
        fig.autofmt_xdate()
    else:
        ax.text(0.5, 0.5, "No data in last 10s", ha="center", va="center",
                transform=ax.transAxes)
        ax.axhline(y=max_size, color="r", linestyle="--", label=f"Max ever = {max_size} B")

    ax.set_xlabel("Timestamp")
    ax.set_ylabel("Bucket Size (bytes)")
    ax.set_title(f"S3 Bucket Size Over Last 10 Seconds — {BUCKET_NAME}")
    ax.legend()
    ax.grid(True, alpha=0.3)

    # Save to buffer and upload
    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    buf.seek(0)
    plt.close(fig)

    s3.put_object(Bucket=BUCKET_NAME, Key="plot", Body=buf.getvalue(),
                  ContentType="image/png")

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"message": "Plot generated and saved to S3."})
    }