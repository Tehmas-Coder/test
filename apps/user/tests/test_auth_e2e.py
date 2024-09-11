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


class AuthE2EUnitTest(TestSetUp):
    fixtures = ["role_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_token_refresh(self, request_data):
        print_test_header("token-refresh")
        url = "/api/refresh/"
        response = self.client.post(url, data=request_data)
        print_test_passed()
        return response

    def do_logout(self, request_data):
        print_test_header("logout")
        url = "/api/logout/"
        response = self.client.post(url, headers=self.headers, data=request_data)
        print_test_passed()
        return response


class AuthE2ETest(AuthE2EUnitTest):
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
    def test_case(self):
        self.failed_missing_refresh_token_test()
        self.failed_null_refresh_token_test()
        self.successfull_refresh_token_test()
        self.failed_old_refresh_token_test()
        self.logout_test()
        self.whole_flow_test()

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    # * failure test because of missing refresh token
    def failed_missing_refresh_token_test(self):
        response = self.do_token_refresh({})
        bad_request_failure_response(self, response)

    # * failure test because of null refresh token
    def failed_null_refresh_token_test(self):
        request_data = {
            "refresh": "",
        }
        response = self.do_token_refresh(request_data)
        bad_request_failure_response(self, response)

    # * Success test because refresh token is present
    def successfull_refresh_token_test(self):
        request_data = {
            "refresh": self.tokens,
        }
        response = self.do_token_refresh(request_data)
        self.headers["refresh"] = response.data["refresh"]  # type: ignore
        validate_success_response_with_token_check(self, response)

    # * failure test because of old refresh token
    def failed_old_refresh_token_test(self):
        request_data = {
            "refresh": self.tokens,
        }
        response = self.do_token_refresh(request_data)
        authorize_failure_response(self, response)

    # * success test because refresh tokens are being provided
    def logout_test(self):
        # self.headers["refresh"] = self.tokens
        request_body = {"refresh": self.headers["refresh"]}
        response = self.do_logout(request_body)
        validate_success_response(self, response)

    # * test to check the whole flow for tokens from register => login => logout
    def whole_flow_test(self):
        response = RegisterUnitTest.do_register(self, json.dumps(self.test_user))  # type: ignore
        validate_success_create_response(self, response)

        # * upon again registering user should not be able to register
        response = RegisterUnitTest.do_register(self, json.dumps(self.test_user))  # type: ignore
        bad_request_failure_response(self, response)

        new_user_data = BaseUser.objects.get(email=self.test_user["email"])
        new_user_data.__dict__["is_verified"] = True
        new_user_data.save()

        response = self.custom_login(self.test_user["email"], self.test_user["password"])
        self.successfull_refresh_token_test()

        self.custom_login(self.test_user["email"], self.test_user["password"])
        self.logout_test()


# ?###################################################
# ?              VALIDATION FUNCTIONS
# ?###################################################
def authorize_failure_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_401_UNAUTHORIZED,
        f" 'status_code' 401 was expected, but received 'status_code' ({response_status_code})",
    )


def bad_request_failure_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_400_BAD_REQUEST,
        f" 'status_code' 400 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_success_response_with_token_check(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_200_OK,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )

    json_data = response.data

    self.assertIn("access", json_data)
    self.assertIn("refresh", json_data)


def validate_success_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_200_OK,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_success_create_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_201_CREATED,
        f" 'status_code' 201 was expected, but received 'status_code' ({response_status_code})",
    )
