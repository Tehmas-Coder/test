import json

from rest_framework import status

from apps.exam_public.tests.test_candidate_exam import CandidateExamUnitTest
from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class AttemptCandidateExamUnitTest(TestSetUp):
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
        "question_subject_seed",
        "question_subject_country_seed",
        "question_retry_hint_seed",
        "question_choice_seed",
        "question_tag_seed",
        "section_seed",
        "subsection_seed",
        "exam_subject_question_seed",
        "schedule_seed",
        "organization_seed",
        "role_seed",
        "user_seed",
        "candidate_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_attempt_one_candidate_exam(self, request_body):
        print_test_header("Attempt_candidate_exam")
        url = "/api/candidate-exam/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data[0]  # type: ignore


class AttemptCandidateExamTest(AttemptCandidateExamUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "candidates": [
            "cyberaxescandidate@gmail.com",
        ],
        "exam": 1,
        "schedule": 2,
        "exam_duration": 120,
    }
    list_of_fields_of_candidate_exam_model = [
        "id",
        "candidate",
        "exam_backlog",
        "schedule",
        "is_preparatory",
        "start_datetime",
        "end_datetime",
        "exam_duration",
        "waiting_duration",
        "extra_duration",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_candidate_exam(self):
        self.successfull_attemptation_of_an_exam_test()

    def successfull_attemptation_of_an_exam_test(self):
        candidate_exam = CandidateExamUnitTest.do_create_candidate_exam(self, json.dumps(self.reuseable_request_body))  # type: ignore
        debug_print(candidate_exam)
        # json_data = self.do_attempt_one_candidate_exam(json.dumps(self.reuseable_request_body))
        # for one_field in self.list_of_fields_of_candidate_exam_model:
        #     self.assertIn(one_field, json_data)


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
