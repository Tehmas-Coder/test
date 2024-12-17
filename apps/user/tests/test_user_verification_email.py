import json

from cryptography.fernet import Fernet
from rest_framework import status

from apps.user.models.user_models import BaseUser
from apps.user.tests.test_user import UserUnitTest
from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    get_encryption_key,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class UserVerificationUnitTest(TestSetUp):
    fixtures = ["country_test_seed", "role_seed", "user_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_resend_verification_link(self, request_body):
        print_test_header("resend_verification_link")
        url = "/api/resend-verification-link/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        return response

    def do_verify_link(self, request_body):
        print_test_header("verification_link")
        url = f"/api/verification?token={request_body}"
        response = self.client.get(
            url,
            headers=self.headers,
        )
        return response


class UserVerificationTest(UserVerificationUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "email": "test_verification@gmail.com",
        "first_name": "umer",
        "last_name": "sheryar",
        "password": "123456789",
        "date_of_birth": "1995-07-27",
        "phone": "+9323346489529",
        "roles": [4],
    }
    list_of_fields_of_user_model = [
        "id",
        "email",
        "first_name",
        "last_name",
        "created_at",
        "updated_at",
        "otp",
        "is_verified",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_user(self):
        UserUnitTest.do_create_user(self, json.dumps(self.reuseable_request_body))  # type: ignore
        created_user_dict = BaseUser.objects.last().__dict__
        self.successfull_resending_of_verification_email_test(created_user_dict)
        self.successfull_verification_of_email(created_user_dict)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successfull_resending_of_verification_email_test(self, created_user_dict):
        request_body = {"email": created_user_dict["email"]}
        response = self.do_resend_verification_link(json.dumps(request_body))
        validate_success_200_test_response(self, response)

    def successfull_verification_of_email(self, created_user_dict):
        key = get_encryption_key()
        cipher = Fernet(key)
        encryption_data = {"email": created_user_dict["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())
        token_data = encrypted_email.decode("utf-8")
        response = self.do_verify_link(token_data)
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


def validate_success_201_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_201_CREATED:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)

    self.assertEqual(
        response_status_code,
        status.HTTP_201_CREATED,
        f" 'status_code' 201 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_success_204_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_204_NO_CONTENT:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)
    self.assertEqual(
        response_status_code,
        status.HTTP_204_NO_CONTENT,
        f" 'status_code' 204 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_failed_404_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_404_NOT_FOUND:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)
    self.assertEqual(
        response_status_code,
        status.HTTP_404_NOT_FOUND,
        f" 'status_code' 404 was expected, but received 'status_code' ({response_status_code})",
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
