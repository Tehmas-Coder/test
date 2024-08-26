import copy
import json

from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class CandidateExamUnitTest(TestSetUp):
    fixtures = [
        "question_type_seed",
        "measuring_unit_seed",
        "subject_seed",
        "education_level_seed",
        "subject_education_level_seed",
        "exam_seed",
        "exam_subject_seed",
        "timezone_test_seed",
        "currency_test_seed",
        "language_test_seed",
        "country_test_seed",
        "media_type_seed",
        "tag_seed",
        "difficulty_level_seed",
        "question_seed",
        "section_seed",
        "subsection_seed",
        "exam_subject_question_seed",
        "schedule_seed",
        "organization_seed",
        "role_seed",
        "test_user_seed",
        "candidate_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_candidate_exam(self, request_body):
        print_test_header("create_candidate_exam")
        url = "/api/candidate-exam/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data[0]

    def do_get_candidate_exam_list(self):
        print_test_header("get_candidate_exam_list")
        url = "/api/candidate-exam/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_candidate_exam(self, candidate_exam_id):
        print_test_header("get_one_candidate_exam")
        url = f"/api/candidate-exam/{candidate_exam_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_update_one_candidate_exam(self, candidate_exam_id, request_body):
        print_test_header("update_candidate_exam")
        url = f"/api/candidate-exam/{candidate_exam_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_200_test_response(self, response)
        return response.data


class CandidateExamTest(CandidateExamUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "candidates": [
            1,
        ],
        "exam": 2,
        "schedule": 2,
    }
    list_of_fields_of_candidate_exam_model = [
        "id",
        "candidate",
        "exam_backlog",
        "schedule",
        "obtained_marks",
        "is_preparatory",
        "date",
        "start_time",
        "end_time",
        "waiting_duration",
        "extra_duration",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_candidate_exam(self):
        self.successfull_creation_of_a_record_test()
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        test_record_id = self.successsfull_fetching_of_one_record_test(list_of_records)
        # self.successfull_updation_of_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        json_data = self.do_create_candidate_exam(json.dumps(self.reuseable_request_body))
        for one_field in self.list_of_fields_of_candidate_exam_model:
            self.assertIn(one_field, json_data)

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_candidate_exam_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_candidate_exam_model in self.list_of_fields_of_candidate_exam_model:
                self.assertIn(
                    one_value_from_list_of_fields_of_candidate_exam_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_candidate_exam_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_candidate_exam_id = list_of_records[len(list_of_records) - 1]["id"]
        json_data = self.do_get_one_candidate_exam(test_candidate_exam_id)
        self.assertEqual(
            json_data["id"],
            test_candidate_exam_id,
            f"The field id ({json_data['id']} is not equal to id ({test_candidate_exam_id}) )",
        )
        return test_candidate_exam_id

    # def successfull_updation_of_record_test(self, test_record_id):
    #     updated_request_body = copy.deepcopy(self.reuseable_request_body)
    #     updated_request_body["organization"] = 3
    #     updated_response_json_data = self.do_update_one_candidate_exam(test_record_id, json.dumps(updated_request_body))
    #     self.assertEqual(updated_response_json_data["id"], test_record_id)


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
