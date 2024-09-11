from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class MeasuringUnitUnitTest(TestSetUp):
    fixtures = ["measuring_unit_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_get_measuring_unit_list(self):
        print_test_header("get_measuring_unit_list")
        url = "/api/measuring-units/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_get_one_measuring_unit(self, measuring_unit_id):
        print_test_header("get_one_measuring_unit")
        url = f"/api/measuring-units/{measuring_unit_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore


class MeasuringUnitTest(MeasuringUnitUnitTest):
    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_measuring_unit(self):
        measuring_units_list = self.successfull_measuring_units_list_get_test()
        self.successfull_get_one_measuring_unit_from_measuring_unit_list(measuring_units_list)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successfull_measuring_units_list_get_test(self):
        json_data = self.do_get_measuring_unit_list()
        self.assertGreater(len(json_data), 0)
        for one_dict in json_data:
            self.assertIn("name", one_dict)
            self.assertIn("code", one_dict)
            self.assertIn("abbreviation", one_dict)
        return json_data

    def successfull_get_one_measuring_unit_from_measuring_unit_list(self, measuring_units_list):
        json_data = measuring_units_list
        test_measuring_unit_id = json_data[len(json_data) - 1]["id"]
        json_data = self.do_get_one_measuring_unit(test_measuring_unit_id)
        self.assertEqual(json_data["id"], test_measuring_unit_id)
        self.assertIn("name", json_data)
        self.assertIn("code", json_data)
        self.assertIn("abbreviation", json_data)


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
