import logging
import os
import time
from datetime import datetime, timezone


class LoggingMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        end_time = time.time()
        duration = (end_time - start_time) * 1000
        user = request.user.id if request.user.is_authenticated else "anonymous"
        log_directory = f"media/logs/{user}/{str(datetime.today().date())}"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        logger = logging.getLogger("")
        handler = logging.FileHandler(filename=f"{log_directory}/{datetime.now(timezone.utc).strftime('%H')}.log")
        formatter = logging.Formatter("%(asctime)s %(message)s")
        formatter.converter = time.gmtime
        formatter._fmt = "%Y-%m-%d %H:%M:%S %Z %(message)s"
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        log_data = {
            "Time Taken (ms)": duration.__ceil__(),
            "Request": {
                "method": request.method,
                "path": request.path,
                "user": user,
                "query_params": str(request.GET) if request.GET else None,
                "data": request.body if request.method == "POST" else None,
            },
            "Response": {
                "status_code": response.status_code,
                # "data": response.content if response.status_code != 500 else None,
            },
        }
        logger.info(f"{log_data}")

        return response
