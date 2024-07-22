import copy, json

from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from core.test_setup import TestSetUp
from rest_framework import status


class QuestionTypeUnitTest(TestSetUp):
    fixtures = ["question_type_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def do_get_question_type_list(self):
        print_test_header("get_question_type_list")
        url = "/api/question-types/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_question_type(self, question_type_id):
        print_test_header("get_one_question_type")
        url = f"/api/question-types/{question_type_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data


class QuestionTypeTest(QuestionTypeUnitTest):
    # * These are defined here so these can be accessed by all the functions
    list_of_fields_of_question_type_model = [
        "id",
        "name",
        "abbreviation",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_question_type(self):
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        self.successsfull_fetching_of_one_record_test(list_of_records)

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_question_type_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_question_type_model in (self.list_of_fields_of_question_type_model):
                self.assertIn(
                    one_value_from_list_of_fields_of_question_type_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_question_type_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_question_type_id = list_of_records[len(list_of_records) - 1]["id"]
        json_data = self.do_get_one_question_type(test_question_type_id)
        self.assertEqual(
            json_data["id"],
            test_question_type_id,
            f"The Field ID ({json_data['id']} is not equal to id ({test_question_type_id}) )",
        )
        for one_value_from_list_of_fields_of_question_type_model in (self.list_of_fields_of_question_type_model):
            self.assertIn(
                one_value_from_list_of_fields_of_question_type_model,
                json_data,
                f"The key {one_value_from_list_of_fields_of_question_type_model} is not present in {json_data}",
            )


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
