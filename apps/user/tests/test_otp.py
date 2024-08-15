import copy
import json

from rest_framework import status

from apps.user.models import BaseUser
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
    fixtures = []

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_verify_otp(self, request_data, user_id):
        print_test_header("verify otp")
        url = f"/api/users/{user_id}/verify-otp/"
        response = self.client.post(url, data=request_data)
        return response

    def do_resend_otp(self, user_id):
        print_test_header("resend otp")
        url = f"/api/users/{user_id}/resend-otp/"
        response = self.client.post(url)
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
        user_id = RegisterUnitTest.do_register(self, json.dumps(test_user)).data["id"]

        # * Test functions are being called here
        self.failed_test_verification_otp_not_valid(user_id)
        self.successfull_test_resend_otp(user_id)
        self.successfull_test_verification_otp(user_id)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def failed_test_verification_otp_not_valid(self, user_id):
        request_data = {"otp": "1234"}
        response = self.do_verify_otp(request_data, user_id)
        validate_failed_400_test_response(self, response)

    def successfull_test_resend_otp(self, user_id):
        response = self.do_resend_otp(user_id)
        validate_success_200_test_response(self, response)

    def successfull_test_verification_otp(self, user_id):
        user = BaseUser.objects.get(id=user_id)
        otp = UserUnitTest.do_get_one_user(self, user_id)["otp"]
        request_data = {
            "otp": otp,
        }
        response = self.do_verify_otp(request_data, user_id)
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
