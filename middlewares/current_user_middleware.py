from threading import local

from rest_framework_simplejwt.authentication import JWTAuthentication

_user = local()


class CurrentUserMiddleware:
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
    return getattr(_user, "value", None)
