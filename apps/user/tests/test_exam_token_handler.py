from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class ExamTokenHandlerUnitTest(TestSetUp):
    fixtures = [
        "country_test_seed",
        "role_seed",
        "user_seed",
        "candidate_seed",
        "organization_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_handle_exam_token(self, request_data):
        print_test_header("exam-token-handler")
        url = "/api/exam-token-handler/"
        response = self.client.post(url, data=request_data)
        return response


class ExamTokenHandlerTest(ExamTokenHandlerUnitTest):
    reusable_request_body = {
        "first_name": "test",
        "last_name": "123",
        "country": 1,
        "token": "gAAAAABndTr3-Ux7ZES1xFLcdRvDtC_A70oU4gl1XQ-Gk9rhFQwzgFR7APLVuY990tSg-wkbi71hSeB-LXtx07nFunqCAW0EXDu7as4BcuHs9EbJCJ5oU5s6WCW4sgFTngbfOCzxW8DfwEW2J3_bYSRSwz1MjgxaUUzAk_I9FkZ7G6-oNv9xU1B9H9BVZqkVPjUfVqYdV96pdhbFbdBvSkOA3C62Rs7P0w==",
    }

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_exam_token(self):
        self.missing_fields_exam_token_handling_test()
        self.successful_exam_token_handling_test()
        self.failed_exam_token_handling_test()

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def missing_fields_exam_token_handling_test(self):
        incomplete_request_body = self.reusable_request_body.copy()
        del incomplete_request_body["first_name"]
        response = self.do_handle_exam_token(incomplete_request_body)
        validate_success_200_test_response(self, response)
        json_data = response.data  # type: ignore
        self.assertEqual(json_data["route"], "get-details")

    def failed_exam_token_handling_test(self):
        invalid_request_body = self.reusable_request_body.copy()
        invalid_request_body["token"] = "invalid_token"
        response = self.do_handle_exam_token(invalid_request_body)
        validate_failed_400_test_response(self, response)
        json_data = response.data  # type: ignore
        self.assertEqual(json_data["status"], "error")
        self.assertEqual(json_data["message"], "Invalid Token")

    def successful_exam_token_handling_test(self):
        response = self.do_handle_exam_token(self.reusable_request_body)
        validate_success_200_test_response(self, response)
        json_data = response.data  # type: ignore
        self.assertIn("route", json_data)
        self.assertIn(json_data["route"], ["login", "register", "exam"])


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
