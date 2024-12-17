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


class CandidateExamAnswerUnitTest(TestSetUp):
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
    def do_create_candidate_exam_answer(self, request_body):
        print_test_header("create_candidate_exam_answer")
        url = "/api/candidate-exam-answer/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            format="multipart",
        )
        validate_success_201_test_response(self, response)
        return response.data  # type: ignore

    def do_get_candidate_exam_answer_list(self):
        print_test_header("get_candidate_exam_answer_list")
        url = "/api/candidate-exam-answer/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_get_one_candidate_exam_answer(self, candidate_exam_answer_id):
        print_test_header("get_one_candidate_exam_answer")
        url = f"/api/candidate-exam-answer/{candidate_exam_answer_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore


class CandidateExamAnswerTest(CandidateExamAnswerUnitTest):
    # * These are defined here so these can be accessed by all the functions
    file_1 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_2 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")

    list_of_fields_of_candidate_exam_answer_model = [
        "id",
        "candidate_exam",
        "exam_backlog_question",
        "exam_backlog_question_choice",
        "exam_backlog_question_choice_title",
        "answer_text",
        "answer_files",
        "seconds_taken",
        "is_attempted",
        "is_correct",
        "score",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_candidate_exam_answer(self):
        self.successfull_creation_of_a_record_test()
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        self.successsfull_fetching_of_one_record_test(list_of_records)

    def successfull_creation_of_a_record_test(self):
        candidate_exam_assignemt_request_body = {
            "candidates": [
                "cyberaxescandidate@gmail.com",
            ],
            "exam": 1,
            "schedule": 2,
            "exam_duration": 120,
        }
        candidate_exam = CandidateExamUnitTest.do_create_candidate_exam(self, json.dumps(candidate_exam_assignemt_request_body))  # type: ignore
        candidate_exam = CandidateExamUnitTest.do_get_one_candidate_exam(self, candidate_exam["id"])  # type: ignore

        request_body = {
            "candidate_exam": candidate_exam["id"],
            "answers": [
                {
                    "exam_backlog_question": candidate_exam["exam_backlog"]["questions"][0]["id"],
                    "exam_backlog_question_choice": candidate_exam["exam_backlog"]["questions"][0]["choices"][0]["id"],
                    "answer_text": None,
                    "answer_files": ["file_1", "file_2"],
                },
            ],
        }
        self.do_create_candidate_exam_answer(
            {
                "data": json.dumps(request_body),
                "file_1": self.file_1,
                "file_2": self.file_2,
            }
        )

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_candidate_exam_answer_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_candidate_exam_answer_model in self.list_of_fields_of_candidate_exam_answer_model:
                self.assertIn(
                    one_value_from_list_of_fields_of_candidate_exam_answer_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_candidate_exam_answer_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_candidate_exam_answer_id = list_of_records[len(list_of_records) - 1]["id"]
        json_data = self.do_get_one_candidate_exam_answer(test_candidate_exam_answer_id)
        self.assertEqual(
            json_data["id"],
            test_candidate_exam_answer_id,
            f"The field id ({json_data['id']} is not equal to id ({test_candidate_exam_answer_id}) )",
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
