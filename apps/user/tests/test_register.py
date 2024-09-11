import copy
import json

from rest_framework import status

from apps.exam_public.models.exam_public_models import Candidate
from core.test_setup import TestSetUp
from utils.rna_utils import (
    color_print,
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class RegisterUnitTest(TestSetUp):
    fixtures = ["role_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_register(self, request_data):
        print_test_header("register")
        url = "/api/register/"
        response = self.client.post(url, data=request_data, content_type="application/json")
        return response


class RegisterTest(RegisterUnitTest):

    test_user = {
        "email": "register_test@gmail.com",
        "first_name": "test",
        "last_name": "123",
        "password": "12345678",
        "date_of_birth": "1995-07-27",
        "phone": "+9323346489529",
    }

    list_of_fields_of_user_model = [
        "id",
        "email",
        "first_name",
        "last_name",
        "full_name",
        "date_of_birth",
        "profile_picture",
        "roles",
        "country",
        "phone",
        "is_verified",
        "is_superuser",
        "date_joined",
        "last_login",
        "description",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################

    def test_cases_register(self):
        self.failed_register_with_no_params_test()
        self.failed_register_with_missing_params_test()
        self.failed_register_with_wrong_email_test()
        self.successfull_register_user_test()
        self.failed_register_user_already_exists_test()

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    # * Failure in case of no paramaters are passed
    def failed_register_with_no_params_test(self):
        response = self.do_register({})
        validate_failed_register_response(self, response)
        print_test_passed()

    # * Failure in case of any required paramater(s) are missing
    def failed_register_with_missing_params_test(self):

        # * Failed because of email is missing
        request_data = copy.deepcopy(self.test_user)
        del request_data["email"]
        response_of_missing_email = self.do_register(json.dumps(request_data))
        validate_failed_register_response(self, response_of_missing_email)
        print_test_passed()

    def failed_register_with_wrong_email_test(self):
        request_data = copy.deepcopy(self.test_user)
        request_data["email"] = "john"
        response = self.do_register(json.dumps(request_data))
        validate_failed_register_response(self, response)
        print_test_passed()

    def successfull_register_user_test(self):
        # -------------------------- Candidate Registration -------------------------- #
        response = self.do_register(json.dumps(self.test_user))
        validate_success_register_response(self, response)
        color_print("## => Candidate Registration")
        print_test_passed()
        json_data = response.data  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in self.test_user:
            if key == "password":
                continue
            self.assertEqual(json_data[key], self.test_user[key])
        candidate_instance = Candidate.objects.filter(user_id=json_data["id"]).first()
        if not candidate_instance:
            color_print("Failed: User created but Candidate not created", "red")

        # -------------------------- SuperUser Registration -------------------------- #

        request_body_for_superuser = copy.deepcopy(self.test_user)
        request_body_for_superuser["email"] = "superuser123@gmail.com"
        request_body_for_superuser["is_superuser"] = True  # type: ignore
        response = self.do_register(json.dumps(request_body_for_superuser))
        validate_success_register_response(self, response)
        color_print("## => SuperUser Registration")
        json_data = response.data  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in request_body_for_superuser:
            if key == "password":
                continue
            self.assertEqual(json_data[key], request_body_for_superuser[key])
        if json_data["is_superuser"]:
            print_test_passed()
        else:
            print_test_failed()

    def failed_register_user_already_exists_test(self):
        response = self.do_register(json.dumps(self.test_user))
        validate_failed_register_response(self, response)
        print_test_passed()


# ?###################################################
# ?              VALIDATION FUNCTIONS
# ?###################################################
def validate_failed_register_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_400_BAD_REQUEST,
        f" 'status_code' 400 was expected, but received 'status_code' ({response_status_code})",
    )


def validate_success_register_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_201_CREATED,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )
