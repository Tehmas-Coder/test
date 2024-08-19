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


class ExamSubjectUnitTest(TestSetUp):
    fixtures = [
        "subject_seed",
        "education_level_seed",
        "subject_education_level_seed",
        "exam_seed",
        "exam_subject_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_exam_subject(self, request_body):
        print_test_header("create_exam_subject")
        url = "/api/exam-subject/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data

    def do_delete_one_exam_subject(self, exam_subject_id):
        print_test_header("delete_exam_subject")
        url = f"/api/exam-subject/{exam_subject_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class ExamSubjectTest(ExamSubjectUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "exam": 2,
        "subject_education_level": 2,
    }
    list_of_fields_of_exam_subject_model = [
        "id",
        "subject_education_level",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_exam_subject(self):
        test_record_id = self.successfull_creation_of_a_record_test()
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        json_data = self.do_create_exam_subject(json.dumps(self.reuseable_request_body))
        for one_field in self.list_of_fields_of_exam_subject_model:
            self.assertIn(one_field, json_data)
        return json_data["id"]

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_exam_subject(test_record_id)


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
