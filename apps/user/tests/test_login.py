import copy
import json

from rest_framework import status

from apps.user.models import BaseUser
from utils.rna_utils import print_test_failed, print_test_header, print_test_passed
from .test_register import RegisterUnitTest
from core.test_setup import TestSetUp
from utils.rna_utils import debug_print


class LoginUnitTest(TestSetUp):
    fixtures = []

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_login(self, request_data):
        print_test_header("login")
        url = "/api/login/"
        response = self.client.post(
            url, data=request_data, content_type="application/json"
        )
        return response


class LoginTest(LoginUnitTest):

    test_user = {
        "email": "register_test@gmail.com",
        "first_name": "test",
        "last_name": "123",
        "password": "12345678",
        "date_of_birth": "1995-07-27",
        "phone": "+9323346489529",
    }

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################

    def test_cases_login(self):
        # * User is registered here for all login test functions
        RegisterUnitTest.do_register(self, json.dumps(self.test_user))

        # * Test functions are being called here
        self.failed_login_user_doesnot_exists()
        self.failed_login_user_missing_params()
        self.successfull_login_test()

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    # * failure case because user doesn't exist in the database
    def failed_login_user_doesnot_exists(self):
        request_data = {"email": "register@gmail.com", "password": "12345678"}
        response = self.do_login(json.dumps(request_data))
        bad_request_login_response(self, response)
        print_test_passed()

    # * failure case because of missing params
    def failed_login_user_missing_params(self):
        request_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"],
        }

        # * Failed because of email is missing
        request_data = copy.deepcopy(request_data)
        del request_data["email"]
        response = self.do_login(json.dumps(request_data))
        bad_request_login_response(self, response)
        print_test_passed()

        # * Failed because of password is missing
        request_data = copy.deepcopy(request_data)
        del request_data["password"]
        response = self.do_login(json.dumps(request_data))
        bad_request_login_response(self, response)
        print_test_passed()

    # * success case user is trying to login with valid credentials
    def successfull_login_test(self):
        new_user_data = BaseUser.objects.get(email=self.test_user["email"])
        new_user_data.__dict__["is_verified"] = True
        new_user_data.save()
        request_data = {
            "email": self.test_user["email"],
            "password": self.test_user["password"],
        }
        response = self.do_login(json.dumps(request_data))
        validate_success_login_response(self, response)
        print_test_passed()


# ?###################################################
# ?              VALIDATION FUNCTIONS
# ?###################################################
def authorize_failure_login_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_401_UNAUTHORIZED,
        f" 'status_code' 401 was expected, but received 'status_code' ({response_status_code})",
    )


def bad_request_login_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_400_BAD_REQUEST,
        f" 'status_code' 400 was expected, but received 'status_code' ({response_status_code})",
    )


def server_error_failure_login_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_500_INTERNAL_SERVER_ERROR,
        f" 'status_code' 500 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_success_login_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_200_OK,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )

    json_data = response.data

    self.assertIn("access", json_data)
    self.assertIn("refresh", json_data)
