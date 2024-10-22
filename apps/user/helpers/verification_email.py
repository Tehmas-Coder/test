import json

from cryptography.fernet import Fernet

from apps.user.models import BaseUser
from core.middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import get_encryption_key, make_error_response


class VerificationEmailNinja:
    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------------------------- #
    #                                Public methods                                #
    # ---------------------------------------------------------------------------- #

    def send_verification_email(self, token):
        user_data = self.__decrypt_token_data(token)
        token_email = user_data["email"]
        self.user_instance: BaseUser = self.__get_user_instance(token_email)  # type: ignore
        self.__check_user_verified_status()
        self.__match_user_email_with_token_email(token_email)
        self.user_instance.is_verified = True
        self.user_instance.save()

    # ---------------------------------------------------------------------------- #
    #                                Private methods                               #
    # ---------------------------------------------------------------------------- #

    def __decrypt_token_data(self, token):
        key = get_encryption_key()
        cipher = Fernet(key)
        decrypt_user_data = cipher.decrypt(token).decode()
        return json.loads(decrypt_user_data)

    def __get_user_instance(self, user_email):
        try:
            user_instance = BaseUser.objects.get(email=user_email)
            return user_instance
        except BaseUser.DoesNotExist:
            ResponseMiddleware.return_now(make_error_response(message="User not found"))

    def __check_user_verified_status(self):
        if self.user_instance.is_verified:
            ResponseMiddleware.return_now(make_error_response(message="User already verified"))

    def __match_user_email_with_token_email(self, email):
        if self.user_instance.email != email:
            ResponseMiddleware.return_now(make_error_response(message="Invalid email"))
