import logging
import os
import sys
import time
from datetime import datetime, timezone

import boto3
from decouple import config


class LoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response
        # S3 variables
        # self.s3_client = boto3.client("s3")
        # self.bucket_name = config("AWS_STORAGE_BUCKET_NAME")

    def __call__(self, request):
        # Skip the logs in Test Environment
        if "test" in sys.argv:
            return self.get_response(request)

        start_time = time.time()

        request_data = {
            "method": request.method,
            "path": request.path,
            "ip_address": request.META.get("REMOTE_ADDR"),
            "query_params": str(request.GET) if request.GET else None,
            "data": request.body if request.method == "POST" else None,
        }

        response = self.get_response(request)

        user = request.user.pk if request.user.is_authenticated else "anonymous"
        end_time = time.time()
        request_data["user"] = user
        duration = (end_time - start_time) * 1000
        log_directory = f"media/logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        log_filename = f"{log_directory}/{str(datetime.today().date())}.log"
        logger = logging.getLogger("")
        handler = logging.FileHandler(filename=log_filename)
        formatter = logging.Formatter("%(asctime)s %(message)s")
        formatter.converter = time.gmtime
        formatter._fmt = "%Y-%m-%d %H:%M:%S %Z %(message)s"
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        log_data = {
            "Time Taken (ms)": duration.__ceil__(),
            "Request": request_data,
            "Response": {
                "status_code": response.status_code,
                "data": response.content if response.status_code != 500 else None,
            },
        }
        logger.info(f"{log_data}")
        logger.removeHandler(handler)
        handler.close()

        # Upload log file to S3
        # s3_log_directory = f"logs/{user}/{str(datetime.today().date())}"
        # s3_log_filename = f"{s3_log_directory}/{datetime.now(timezone.utc).strftime('%H')}.log"
        # self.s3_client.upload_file(log_filename, self.bucket_name, s3_log_filename)

        return response
