from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from apps.user.tests.test_setup import TestSetUp
from rest_framework import status


class CountryUnitTest(TestSetUp):
    fixtures = [
        "currency_test_seed",
        "timezone_test_seed",
        "language_test_seed",
        "country_test_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_get_country_list(self):
        print_test_header("get_country_list")
        url = "/api/countries/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_country(self, country_id):
        print_test_header("get_one_country")
        url = f"/api/countries/{country_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data


class CountryTest(CountryUnitTest):
    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_country(self):
        countries_list = self.successfull_countries_list_get_test()
        self.successfull_get_one_country_from_country_list(countries_list)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successfull_countries_list_get_test(self):
        json_data = self.do_get_country_list()
        self.assertGreater(len(json_data), 0)
        for one_dict in json_data:
            self.assertIn("name", one_dict)
            self.assertIn("iso2_code", one_dict)
            self.assertIn("iso3_code", one_dict)
            self.assertIn("capital", one_dict)
            self.assertIn("lat", one_dict)
            self.assertIn("lon", one_dict)
            self.assertIn("dial_code", one_dict)
            self.assertIn("is_un_member", one_dict)
            self.assertIn("flag", one_dict)
        return json_data

    def successfull_get_one_country_from_country_list(self, countries_list):
        json_data = countries_list
        test_country_id = json_data[len(json_data) - 1]["id"]
        json_data = self.do_get_one_country(test_country_id)
        self.assertEqual(json_data["id"], test_country_id)
        self.assertIn("name", json_data)
        self.assertIn("iso2_code", json_data)
        self.assertIn("iso3_code", json_data)
        self.assertIn("capital", json_data)
        self.assertIn("lat", json_data)
        self.assertIn("lon", json_data)
        self.assertIn("dial_code", json_data)
        self.assertIn("is_un_member", json_data)
        self.assertIn("flag", json_data)
        self.assertIn("timezones", json_data)
        self.assertIn("currencies", json_data)
        self.assertIn("languages", json_data)
        self.assertIn("states", json_data)


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
