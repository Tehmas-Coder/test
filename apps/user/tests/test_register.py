import copy, json

from rest_framework import status

from utils.rna_utils import print_test_header, print_test_passed
from core.test_setup import TestSetUp
from utils.rna_utils import debug_print


class RegisterUnitTest(TestSetUp):
    fixtures = []

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_register(self, request_data):
        print_test_header("register")
        url = "/api/users/"
        response = self.client.post(
            url, data=request_data, content_type="application/json"
        )
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

        # # * Failed because of password is missing
        # request_data = copy.deepcopy(self.test_user)
        # del request_data["password"]
        # response_of_missing_password = self.do_register(json.dumps(request_data))
        # validate_failed_register_response(self, response_of_missing_password)
        # print_test_passed()

    def failed_register_with_wrong_email_test(self):
        request_data = copy.deepcopy(self.test_user)
        request_data["email"] = "john"
        response = self.do_register(json.dumps(request_data))
        validate_failed_register_response(self, response)
        print_test_passed()

    def successfull_register_user_test(self):
        response = self.do_register(json.dumps(self.test_user))
        validate_success_register_response(self, response)
        print_test_passed()

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

    # json_data = response.data
    # api_response_status = json_data["status"]
    # self.assertEqual(
    #     api_response_status,
    #     "failed",
    #     f" Status 'failed' was expected, but received ({api_response_status})",
    # )


def validate_success_register_response(self, response):
    response_status_code = response.status_code
    self.assertEqual(
        response_status_code,
        status.HTTP_201_CREATED,
        f" 'status_code' 200 was expected, but received 'status_code' ({response_status_code})",
    )

    # json_data = response.data
    # api_response_status = json_data["status"]
    # self.assertEqual(
    #     api_response_status,
    #     "success",
    #     f" Status 'success' was expected, but received ({api_response_status})",
    # )

    # api_response_message = json_data["message"]
    # self.assertEqual(
    #     api_response_message,
    #     "Registered Successfully. Please check your email for the OTP.",
    #     f" Status message 'success' was expected, but received ({api_response_message})",
    # )
