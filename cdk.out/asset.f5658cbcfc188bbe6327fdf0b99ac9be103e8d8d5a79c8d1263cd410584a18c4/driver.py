import os
import time
import boto3
import urllib.request

s3 = boto3.client("s3")

BUCKET_NAME = os.environ["BUCKET_NAME"]
API_URL = os.environ["API_URL"]


def handler(event, context):
    # Step 1: Create assignment1.txt
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment1.txt",
                  Body="Empty Assignment 1")
    print("Created assignment1.txt (19 bytes)")
    time.sleep(3)

    # Step 2: Update assignment1.txt
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment1.txt",
                  Body="Empty Assignment 2222222222")
    print("Updated assignment1.txt (28 bytes)")
    time.sleep(3)

    # Step 3: Delete assignment1.txt
    s3.delete_object(Bucket=BUCKET_NAME, Key="assignment1.txt")
    print("Deleted assignment1.txt (0 bytes)")
    time.sleep(3)

    # Step 4: Create assignment2.txt
    s3.put_object(Bucket=BUCKET_NAME, Key="assignment2.txt",
                  Body="33")
    print("Created assignment2.txt (2 bytes)")
    time.sleep(3)

    # Step 5: Call plotting API
    print(f"Calling plotting API: {API_URL}")
    req = urllib.request.Request(API_URL, method="GET")
    with urllib.request.urlopen(req) as resp:
        body = resp.read().decode()
        print(f"Plot API response: {body}")

    return {"statusCode": 200, "body": "Driver completed."}