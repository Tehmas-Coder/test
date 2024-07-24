from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from core.test_setup import TestSetUp
from rest_framework import status


class StateUnitTest(TestSetUp):
    fixtures = ["country_test_seed", "state_test_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_get_state_list(self):
        print_test_header("get_state_list")
        url = "/api/states/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_state(self, state_id):
        print_test_header("get_one_state")
        url = f"/api/states/{state_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data


class StateTest(StateUnitTest):
    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_state(self):
        states_list = self.successfull_states_list_get_test()
        self.successfull_get_one_state_from_state_list(states_list)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successfull_states_list_get_test(self):
        json_data = self.do_get_state_list()
        self.assertGreater(len(json_data), 0)
        for one_dict in json_data:
            self.assertIn("name", one_dict)
            self.assertIn("code", one_dict)
        return json_data

    def successfull_get_one_state_from_state_list(self, states_list):
        json_data = states_list
        test_state_id = json_data[len(json_data) - 1]["id"]
        json_data = self.do_get_one_state(test_state_id)
        self.assertEqual(json_data["id"], test_state_id)
        self.assertIn("name", json_data)
        self.assertIn("code", json_data)


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
