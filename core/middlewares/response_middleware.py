import threading

from django.utils.deprecation import MiddlewareMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

_thread_local = threading.local()


class ResponseMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_local.custom_response = None

    def process_response(self, request, response):
        custom_response = getattr(_thread_local, "custom_response", None)
        if custom_response:
            self._ensure_response_rendered(custom_response)
            return custom_response
        return response

    @staticmethod
    def return_now(response: Response):
        _thread_local.custom_response = response

    @staticmethod
    def _ensure_response_rendered(response):
        if not hasattr(response, "accepted_renderer"):
            response.accepted_renderer = JSONRenderer()
        if not hasattr(response, "accepted_media_type"):
            response.accepted_media_type = "application/json"
        if not hasattr(response, "renderer_context"):
            response.renderer_context = {}
        response.render()
