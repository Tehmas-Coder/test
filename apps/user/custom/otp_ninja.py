from apps.user.models.user_models import BaseUser
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response, make_warning_response


class OTPNinja:
    def __init__(self, email):
        self.email = email
        self.user = BaseUser.get_user_by_email(email)

    def verify_otp(self, otp):
        self.__validate_user()
        if self.user.is_otp_expired:  # type: ignore
            ResponseMiddleware.return_now(make_warning_response(message="OTP expired! Please request for another OTP"))
        if not self.user.verify_otp(otp):  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="Invalid OTP!"))

    def resend_otp(self):
        self.__validate_user()
        if not self.user.is_otp_expired:  # type: ignore
            ResponseMiddleware.return_now(make_warning_response(message="OTP already sent! Please check your email for the OTP"))
        if not self.user.send_otp():  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="Failed to send OTP, please try again"))

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __validate_user(self):
        if not self.user:
            ResponseMiddleware.return_now(make_error_response(message="User not found!"))
        if self.user.is_verified:  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="User is already verified!"))
