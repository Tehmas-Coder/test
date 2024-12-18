import json

from rest_framework import status

from apps.exam_public.models.exam_public_models import CandidateExamAnswer
from apps.exam_public.tests.test_candidate_exam import CandidateExamUnitTest
from apps.exam_public.tests.test_candidate_exam_answer import (
    CandidateExamAnswerUnitTest,
)
from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    decrypt_message,
    get_encryption_key,
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
    def do_attempt_one_sequential_candidate_exam(self, request_body):
        print_test_header("attempt_sequential_candidate_exam")
        url = "/api/attempt-candidate-exam/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
        )
        return response

    def do_submit_candidate_exam(self, candidate_exam_id):
        print_test_header("submit_candidate_exam")
        url = f"/api/candidate-exam/{candidate_exam_id}/submit/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=None,
        )
        validate_success_200_test_response(self, response)
        return response

    def do_mark_candidate_exam(self, request_body):
        print_test_header("mark_candidate_exam")
        url = f"/api/mark-candidate-exam/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_200_test_response(self, response)
        return response

    def do_get_scoresheet_of_candidate_exam(self, candidate_exam_id):
        print_test_header("show_scoresheet_of_candidate_exam")
        url = f"/api/candidate-exam-scoresheet/{candidate_exam_id}/"
        response = self.client.get(
            url,
            headers=self.headers,
        )
        validate_success_200_test_response(self, response)
        return response


class AttemptCandidateExamTest(AttemptCandidateExamUnitTest):
    """
    Attempting a candidate exam
    """

    list_of_fields = ["question", "candidate_exam", "key"]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_candidate_exam(self):
        self.failed_attemptation_of_an_exam_test_missing_candidate_exam_id()
        self.successfull_attemptation_of_an_exam_test()

    def failed_attemptation_of_an_exam_test_missing_candidate_exam_id(self):
        request_body = {
            "exam_status": "attempted",
        }
        response = self.do_attempt_one_sequential_candidate_exam(request_body)
        validate_failed_400_test_response(self, response)

    def successfull_attemptation_of_an_exam_test(self):
        candidate_exam_assignemt_request_body = {
            "candidates": [
                "cyberaxescandidate@gmail.com",
            ],
            "exam": 1,
            "schedule": 2,
            "exam_duration": 120,
        }
        candidate_exam = CandidateExamUnitTest.do_create_candidate_exam(self, json.dumps(candidate_exam_assignemt_request_body))  # type: ignore
        request_body = {
            "candidate_exam_id": candidate_exam["id"],
            "exam_status": "attempted",
        }
        response = self.do_attempt_one_sequential_candidate_exam(request_body)
        validate_success_200_test_response(self, response)
        json_data = response.data  # type: ignore
        for one_field in self.list_of_fields:
            self.assertIn(one_field, json_data)

        # * --------------------------- Submitting an Answer --------------------------- #

        candidate_exam = CandidateExamUnitTest.do_get_one_candidate_exam(self, candidate_exam["id"])  # type: ignore

        request_body = {
            "candidate_exam": candidate_exam["id"],
            "answers": [
                {
                    "exam_backlog_question": candidate_exam["exam_backlog"]["questions"][0]["id"],
                    "exam_backlog_question_choice": candidate_exam["exam_backlog"]["questions"][0]["choices"][0]["id"],
                    "answer_text": None,
                    "answer_files": [],
                },
            ],
        }
        CandidateExamAnswerUnitTest.do_create_candidate_exam_answer(self, request_body={"data": json.dumps(request_body)})  # type: ignore

        # -------------------- Test for sending the next question by sending the latest attempted question id -------------------- #
        encrypted_data = json_data.get("key")
        decrypted_data = json.loads(decrypt_message(encrypted_data, get_encryption_key()))
        all_questions = decrypted_data["all_questions"]
        request_body = {
            "key": encrypted_data,
            "question_backlog_id": all_questions[0]["id"],
        }
        response = self.do_attempt_one_sequential_candidate_exam(request_body)
        validate_success_200_test_response(self, response)
        json_data = response.data  # type: ignore
        for one_field in self.list_of_fields:
            self.assertIn(one_field, json_data)
        self.assertEqual(json_data["question"]["id"], all_questions[1]["id"])

        # * --------------------------- Submitting an Answer --------------------------- #

        request_body = {
            "candidate_exam": candidate_exam["id"],
            "answers": [
                {
                    "exam_backlog_question": candidate_exam["exam_backlog"]["questions"][1]["id"],
                    "exam_backlog_question_choice": None,
                    "answer_text": "Hello Answer",
                    "answer_files": [],
                },
            ],
        }
        CandidateExamAnswerUnitTest.do_create_candidate_exam_answer(self, request_body={"data": json.dumps(request_body)})  # type: ignore

        # -------------------- Test for sending the next question with just the key-------------------- #
        encrypted_data = json_data.get("key")
        decrypted_data = json.loads(decrypt_message(encrypted_data, get_encryption_key()))
        all_questions = decrypted_data["all_questions"]
        request_body = {
            "key": encrypted_data,
        }
        response = self.do_attempt_one_sequential_candidate_exam(request_body)
        validate_success_200_test_response(self, response)
        json_data = response.data  # type: ignore
        for one_field in self.list_of_fields:
            self.assertIn(one_field, json_data)
        self.assertEqual(json_data["question"]["id"], all_questions[2]["id"])

        # * ------------------------------ Exam Submission ----------------------------- #

        self.do_submit_candidate_exam(candidate_exam_id=candidate_exam["id"])

        # * ------------------------------- Exam Marking ------------------------------- #

        candidate_exam_answer_id = list(CandidateExamAnswer.objects.filter(candidate_exam=candidate_exam["id"]).values_list("id", flat=True))[1]
        request_body = {
            "candidate_exam_id": candidate_exam["id"],
            "questions_scores": [
                {
                    "candidate_exam_answer": candidate_exam_answer_id,
                    "score": 10,
                }
            ],
        }
        response = self.do_mark_candidate_exam(json.dumps(request_body))

        # * ------------------------------ Exam Scoresheet ----------------------------- #

        response = self.do_get_scoresheet_of_candidate_exam(candidate_exam_id=candidate_exam["id"])
        self.assertNotEqual(response.data["obtained_marks"], None)  # type: ignore


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


def validate_failed_400_test_response(self, response):
    response_status_code = response.status_code
    if response_status_code == status.HTTP_400_BAD_REQUEST:
        print_test_passed()
    else:
        print_test_failed()
        print(response.content)
    self.assertEqual(
        response_status_code,
        status.HTTP_400_BAD_REQUEST,
        f" 'status_code' 400 was expected, but received 'status_code' ({response_status_code})",
    )
