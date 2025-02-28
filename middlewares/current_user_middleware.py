from threading import local

from rest_framework_simplejwt.authentication import JWTAuthentication

_user = local()


class CurrentUserMiddleware:
    """
    Middleware to set the current user in thread-local storage based on JWT authentication.
    This middleware attempts to authenticate the user using JWT. If authentication is successful,
    the user is stored in thread-local storage for the duration of the request. If authentication
    fails, the user is set to None.
    Attributes:
        get_response (callable): The next middleware or view in the chain to be called.
    Methods:
        __init__(get_response): Initializes the middleware with the next middleware or view.
        __call__(request): Processes the request to authenticate the user and sets the user in thread-local storage.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Authenticate the user using JWT
        try:
            auth_result = JWTAuthentication().authenticate(request)
        except Exception as e:
            auth_result = None
        # If authentication is successful, set the user in _user local thread storage
        if auth_result is not None:
            user, tokens = auth_result
            _user.value = user
        else:
            _user.value = None

        response = self.get_response(request)
        return response


def get_current_user():
    """
    Get the current user from _user local thread storage.

    :return: The current user object or None if no user is set.
    """
    return getattr(_user, "value", None)
