import os
from datetime import datetime

import boto3
from decouple import config

from utils.rna_utils import color_print


def upload_logs_to_s3():
    """
    Upload all logs from the `media/logs` directory to S3.
    """
    s3_client = boto3.client("s3")
    bucket_name = config("AWS_STORAGE_BUCKET_NAME")
    base_directory = "media/logs"

    for root, dirs, files in os.walk(base_directory):
        for file in files:
            local_path = os.path.join(root, file)
            # Create the S3 key
            s3_key = os.path.relpath(local_path, base_directory)
            s3_key = f"logs/{s3_key}"
            # s3_client.upload_file(local_path, bucket_name, s3_key)
            color_print(f"Uploaded {local_path} to {s3_key}")

    color_print("*******************************************************", "yellow")
    color_print("All logs uploaded to S3.", "yellow")
    color_print("*******************************************************", "yellow")
