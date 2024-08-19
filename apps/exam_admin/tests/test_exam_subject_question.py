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


class ExamSubjectQuestionUnitTest(TestSetUp):
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
        "measuring_unit_seed",
        "media_type_seed",
        "tag_seed",
        "difficulty_level_seed",
        "question_seed",
        "section_seed",
        "subsection_seed",
        "exam_subject_question_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_exam_subject_question(self, request_body):
        print_test_header("create_exam_subject_question")
        url = "/api/exam-subject-question/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data

    def do_update_one_exam_subject_question(self, exam_id, request_body):
        print_test_header("update_exam_subject_question")
        url = f"/api/exam-subject-question/{exam_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_200_test_response(self, response)
        return response.data

    def do_delete_one_exam_subject_question(self, exam_subject_question_id):
        print_test_header("delete_exam_subject_question")
        url = f"/api/exam-subject-question/{exam_subject_question_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class ExamSubjectQuestionTest(ExamSubjectQuestionUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "exam_subject": {
            "subject_education_level": 5,
            "exam": 2,
        },
        "question": 1,
        "section": None,
        "subsection": None,
        "sequence": 5,
    }
    list_of_fields_of_exam_subject_question_model = [
        "id",
        "exam_subject",
        "question",
        "section",
        "subsection",
        "sequence",
        "description",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_exam_subject_question(self):
        test_record_id = self.successfull_creation_of_a_record_test()
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        json_data = self.do_create_exam_subject_question(json.dumps(self.reuseable_request_body))
        for one_field in self.list_of_fields_of_exam_subject_question_model:
            self.assertIn(one_field, json_data)
        return json_data["id"]

    def successfull_updation_of_record_test(self, test_record_id):
        updated_request_body = copy.deepcopy(self.reuseable_request_body)
        updated_request_body["section"] = 1
        updated_request_body["subsection"] = 2
        updated_request_body["sequence"] = 1
        updated_response_json_data = self.do_update_one_exam_subject_question(test_record_id, json.dumps(updated_request_body))
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in updated_request_body:
            if key in ["section", "subsection", "sequence"]:
                self.assertEqual(updated_response_json_data[key], updated_request_body[key])

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_exam_subject_question(test_record_id)


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
