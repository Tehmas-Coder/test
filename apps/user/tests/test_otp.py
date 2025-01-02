import copy
import json
import time

from rest_framework import status

from apps.user.models.user_models import BaseUser
from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)

from .test_register import RegisterUnitTest
from .test_user import UserUnitTest


class OTPUnitTest(TestSetUp):
    fixtures = ["role_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_verify_otp(self, request_data):
        print_test_header("verify otp")
        url = f"/api/verify-otp/"
        response = self.client.post(url, data=request_data)
        return response

    def do_resend_otp(self, request_data):
        print_test_header("resend otp")
        url = f"/api/resend-otp/"
        response = self.client.post(url, data=request_data)
        return response


class OTPTest(OTPUnitTest):

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################

    def test_cases_otp(self):
        # * User is regsitered here for all otp test functions
        test_user = {
            "email": "register_test@gmail.com",
            "first_name": "test",
            "last_name": "123",
            "password": "12345678",
            "date_of_birth": "1995-07-27",
            "phone": "+9323346489529",
        }
        user_id = RegisterUnitTest.do_register(self, json.dumps(test_user)).data["id"]  # type: ignore

        # * Test functions are being called here
        self.failed_test_verification_otp_not_valid()
        # self.successfull_test_resend_otp()
        self.successfull_test_verification_otp(user_id)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def failed_test_verification_otp_not_valid(self):
        request_data = {
            "email": "register_test@gmail.com",
            "otp": "1234",
        }
        response = self.do_verify_otp(request_data)
        validate_failed_400_test_response(self, response)

    def successfull_test_resend_otp(self):
        request_data = {
            "email": "register_test@gmail.com",
        }
        response = self.do_resend_otp(request_data)
        validate_success_200_test_response(self, response)

    def successfull_test_verification_otp(self, user_id):
        otp = UserUnitTest.do_get_one_user(self, user_id)["otp"]  # type: ignore
        request_data = {
            "email": "register_test@gmail.com",
            "otp": otp,
        }
        response = self.do_verify_otp(request_data)
        validate_success_200_test_response(self, response)


# ?###################################################
# ?              VALIDATION FUNCTIONS
# ?###################################################
def validate_success_200_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_200_OK:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)
    self.assertEqual(
        response_status_code,
        status.HTTP_200_OK,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_failed_400_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_400_BAD_REQUEST:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)
    self.assertEqual(
        response_status_code,
        status.HTTP_400_BAD_REQUEST,
        f" 'status_code' 400 was expected, but received 'status_code' ({response_status_code})",
    )
