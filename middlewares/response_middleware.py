import threading

from django.utils.deprecation import MiddlewareMixin
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response

_thread_local = threading.local()


class ImmediateHttpResponse(Exception):
    def __init__(self, response):
        self.response = response


class ResponseMiddleware(MiddlewareMixin):
    """
    This middleware allows views to return a response immediately without going through the rest of the middleware chain.

    To return a response immediately, use the `return_now` method of this middleware.

    Example:
    ```
    from middlewares.response_middleware import ResponseMiddleware

    def my_view(request):
        response = Response({"message": "Hello, World!"})
        ResponseMiddleware.return_now(response)
    ```

    The response will be returned immediately without going through the rest of code and middleware chain.
    """

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
        raise ImmediateHttpResponse(response)

    @staticmethod
    def _ensure_response_rendered(response):
        if not hasattr(response, "accepted_renderer"):
            response.accepted_renderer = JSONRenderer()
        if not hasattr(response, "accepted_media_type"):
            response.accepted_media_type = "application/json"
        if not hasattr(response, "renderer_context"):
            response.renderer_context = {}
        response.render()

    def process_exception(self, request, exception):
        if isinstance(exception, ImmediateHttpResponse):
            self._ensure_response_rendered(exception.response)
            return exception.response
        return None
