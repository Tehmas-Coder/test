from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from apps.user.tests.test_setup import TestSetUp
from rest_framework import status


class CurrencyUnitTest(TestSetUp):
    fixtures = ["currency_test_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_get_currency_list(self):
        print_test_header("get_currency_list")
        url = "/api/currencies/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_currency(self, currency_id):
        print_test_header("get_one_currency")
        url = f"/api/currencies/{currency_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data


class CurrencyTest(CurrencyUnitTest):
    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_currency(self):
        currencies_list = self.successfull_currencies_list_get_test()
        self.successfull_get_one_currency_from_currency_list(currencies_list)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successfull_currencies_list_get_test(self):
        json_data = self.do_get_currency_list()
        self.assertGreater(len(json_data), 0)
        for one_dict in json_data:
            self.assertIn("name", one_dict)
            self.assertIn("code", one_dict)
            self.assertIn("symbol", one_dict)
        return json_data

    def successfull_get_one_currency_from_currency_list(self, currencies_list):
        json_data = currencies_list
        test_currency_id = json_data[len(json_data) - 1]["id"]
        json_data = self.do_get_one_currency(test_currency_id)
        self.assertEqual(json_data["id"], test_currency_id)
        self.assertIn("name", json_data)
        self.assertIn("code", json_data)
        self.assertIn("symbol", json_data)


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
