import json

from cryptography.fernet import Fernet
from decouple import config

from apps.user.models import BaseUser
from core.middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import (
    generate_random_password,
    get_encryption_key,
    make_error_response,
)


class VerificationEmailNinja:
    def __init__(self) -> None:
        pass

    # ---------------------------------------------------------------------------- #
    #                                Public methods                                #
    # ---------------------------------------------------------------------------- #

    def send(self, token):
        user_data = self.__decrypt_token_data(token)
        token_email = user_data["email"]
        user_instance: BaseUser = self.__get_user_instance(token_email)  # type: ignore
        self.__check_user_verified_status(user_instance)
        self.__match_user_email_with_token_email(token_email, user_instance)
        user_instance.is_verified = True
        user_instance.save()

    def resend(self, email):
        user_instance: BaseUser = self.__get_user_instance(email)  # type: ignore
        self.__check_user_verified_status(user_instance)
        self.__send_verification_email(user_instance)

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
            user_instance = BaseUser.get_user_by_email(user_email)
            return user_instance
        except BaseUser.DoesNotExist:
            ResponseMiddleware.return_now(make_error_response(message="User not found"))

    def __check_user_verified_status(self, user_instance: BaseUser):
        if user_instance.is_verified:
            ResponseMiddleware.return_now(make_error_response(message="User already verified"))

    def __match_user_email_with_token_email(self, email, user_instance: BaseUser):
        if user_instance.email != email:
            ResponseMiddleware.return_now(make_error_response(message="Invalid link"))

    def __send_verification_email(self, user_instance: BaseUser):
        new_password = generate_random_password()
        user_instance.set_password(new_password)
        user_instance.save()

        key = get_encryption_key()
        cipher = Fernet(key)

        encryption_data = {"email": user_instance.email}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())
        token_data = encrypted_email.decode("utf-8")

        url = config("QB_PUBLIC_FE_URL")
        final_url = f"{url}verification?token={token_data}"

        send_email_data_dict = {
            "first_name": user_instance.first_name,
            "last_name": user_instance.last_name,
            "email": user_instance.email,
            "password": new_password,
            "URL": final_url,
        }

        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_url():
            ResponseMiddleware.return_now(make_error_response(message="Failed to send verification link."))
        del email_notification_ninja
