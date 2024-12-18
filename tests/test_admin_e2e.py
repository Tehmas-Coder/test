import json

from rest_framework import status
from rest_framework.response import Response

from apps.lookups.tests.test_tag import TagUnitTest
from apps.organization.tests.test_organization import OrganizationUnitTest
from apps.questionbank.tests.test_education_level import EducationLevelUnitTest
from apps.questionbank.tests.test_question_attempt_response import (
    QuestionAttemptResponseUnitTest,
)
from apps.questionbank.tests.test_question_choice import QuestionChoiceUnitTest
from apps.questionbank.tests.test_question_choice_media import (
    QuestionChoiceMediaUnitTest,
)
from apps.questionbank.tests.test_question_e2e import QuestionUnitTest
from apps.questionbank.tests.test_question_media import QuestionMediaUnitTest
from apps.questionbank.tests.test_question_retry_hint import QuestionRetryHintUnitTest
from apps.questionbank.tests.test_question_retry_hint_media import (
    QuestionRetryHintMediaUnitTest,
)
from apps.questionbank.tests.test_question_tag import QuestionTagUnitTest
from apps.questionbank.tests.test_subject import SubjectUnitTest
from apps.questionbank.tests.test_subject_education_level import (
    SubjectEducationLevelUnitTest,
)
from apps.user.models.user_models import BaseUser
from apps.user.tests.test_login import LoginUnitTest
from apps.user.tests.test_user import UserUnitTest
from core.test_setup import TestSetUp
from utils.rna_utils import debug_print, print_test_failed, print_test_passed


class AdminEndToEndTest(TestSetUp):
    question_file = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    question_choice_file = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    question_retry_hint_file = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")

    fixtures = [
        "timezone_test_seed",
        "currency_test_seed",
        "language_test_seed",
        "country_test_seed",
        "media_type_seed",
        "measuring_unit_seed",
        "tag_seed",
        "package_seed",
        "user_seed",
        "role_seed",
        "user_role_seed",
        "permission_seed",
        "resource_seed",
        "role_permission_seed",
        "organization_seed",
        "organization_package_seed",
        "organization_user_seed",
        "question_type_seed",
        "education_level_seed",
        "difficulty_level_seed",
        "subject_seed",
        "subject_education_level_seed",
        "question_seed",
        "question_subject_seed",
        "question_subject_country_seed",
        "question_choice_seed",
        "question_retry_hint_seed",
        "question_tag_seed",
        "schedule_seed",
        "exam_seed",
        "section_seed",
        "subsection_seed",
        "exam_subject_seed",
        "exam_subject_question_seed",
        "candidate_seed",
    ]

    def test_admin_e2e(self):
        # ---------------------------- Organization Creation --------------------------- #
        organization_request_body = {
            "name": "Test Org",
            "country": 1,
            "package": 1,
        }
        organization_response: dict = OrganizationUnitTest.do_create_organization(self, json.dumps(organization_request_body))  # type: ignore
        request_response_values_asserter(self, organization_request_body, organization_response)

        # ------------------------ Organization User Creation ------------------------ #
        user_request_body = {
            "organization": organization_response["id"],
            "email": "test_admin@gmail.com",
            "first_name": "test",
            "last_name": "admin",
            "password": "123456789",
            "date_of_birth": "1995-07-27",
            "country": 1,
            "phone": "+9323346489529",
            "roles": [1],
            "description": "This user is admin of test org",
        }
        user_response: Response = UserUnitTest.do_create_user(self, json.dumps(user_request_body))  # type: ignore
        validate_success_201_test_response(self, user_response)
        request_response_values_asserter(self, user_request_body, user_response.data)  # type: ignore

        # ------------------------- Verify Organization User ------------------------- #
        user_instance: BaseUser = BaseUser.objects.last()  # type: ignore
        user_instance.is_verified = True
        user_instance.save()

        # ------------------------- Log in Organization User ------------------------- #
        login_request_body = {
            "email": user_request_body["email"],
            "password": user_request_body["password"],
        }
        self.custom_login(email=user_request_body["email"], password=user_request_body["password"])
        login_response: Response = LoginUnitTest.do_login(self, json.dumps(login_request_body))  # type: ignore
        validate_success_200_test_response(self, login_response)

        # ------------------------------- Tag Creation ------------------------------- #
        tag_request_body = {
            "name": "Test Tag",
            "code": "TT",
            "abbreviation": "TT",
        }
        tag_response: dict = TagUnitTest.do_create_tag(self, json.dumps(tag_request_body))  # type: ignore
        request_response_values_asserter(self, tag_request_body, tag_response)

        # ------------------------- Education Level Creation ------------------------- #
        education_level_request_body = {
            "name": "Test Education Level",
            "code": "TEL",
            "abbreviation": "TEL",
        }
        education_level_response: dict = EducationLevelUnitTest.do_create_education_level(self, json.dumps(education_level_request_body))  # type: ignore
        request_response_values_asserter(self, education_level_request_body, education_level_response)

        # ----------------------------- Subject Creation ----------------------------- #
        subject_request_body = {
            "name": "Test Subject",
            "code": "TS",
            "abbreviation": "TS",
        }
        subject_response: dict = SubjectUnitTest.do_create_subject(self, json.dumps(subject_request_body))  # type: ignore
        request_response_values_asserter(self, subject_request_body, subject_response)

        # ---------------------- SubjectEducationLevel Creation ---------------------- #
        subject_education_level_request_body = {
            "subject": subject_response["id"],
            "education_level": education_level_response["id"],
        }
        subject_education_level_response: dict = SubjectEducationLevelUnitTest.do_create_subject_education_level(self, json.dumps(subject_education_level_request_body))  # type: ignore
        request_response_values_asserter(self, subject_education_level_request_body, subject_education_level_response)

        # ----------------------------- Question Creation ---------------------------- #
        question_request_body = {
            "title": "Test Question",
            "type": 2,
            "subjects": [
                {
                    "difficulty_level": 1,
                    "subject_education_level": {
                        "subject": subject_response["id"],
                        "education_level": education_level_response["id"],
                    },
                    "is_global": 1,
                    "measuring_unit": 1,
                    "time_limit": 12,
                    "total_marks": 5,
                    "is_optional": 0,
                },
            ],
            "max_retries": 2,
            "retry_penalty": 1,
            "can_shuffle": 1,
            "has_media": 0,
        }
        question_response: dict = QuestionUnitTest.do_create_question(self, {"data": json.dumps(question_request_body)})  # type: ignore
        del question_request_body["subjects"]
        request_response_values_asserter(self, question_request_body, question_response)

        # -------------------------- Question Media Creation ------------------------- #
        question_media_request_body = {
            "question": question_response["id"],
            "media": self.question_file,
        }
        question_media_response: dict = QuestionMediaUnitTest.do_create_question_media(self, question_media_request_body)  # type: ignore

        # ------------------------- Question Choice Creation ------------------------- #
        question_choice_request_body = {
            "question": question_response["id"],
            "title": "Test Choice",
            "text": "",
            "weight": 100,
            "is_negative_weight": 0,
            "is_correct": 1,
            "has_media": 0,
        }
        question_choice_response: dict = QuestionChoiceUnitTest.do_create_question_choice(self, question_choice_request_body)  # type: ignore
        request_response_values_asserter(self, question_choice_request_body, question_choice_response)

        # ---------------------- Question Choice Media Creation ---------------------- #
        question_choice_media_request_body = {
            "question_choice": question_choice_response["id"],
            "media": self.question_choice_file,
        }
        question_choice_media_response: dict = QuestionChoiceMediaUnitTest.do_create_question_choice_media(self, question_choice_media_request_body)  # type: ignore

        # ----------------------- Question Retry Hint Creation ----------------------- #
        question_retry_hint_request_body = {
            "question": question_response["id"],
            "text": "Test Hint",
            "has_media": 0,
        }
        question_retry_hint_response: dict = QuestionRetryHintUnitTest.do_create_question_retry_hint(self, question_retry_hint_request_body)  # type: ignore
        request_response_values_asserter(self, question_retry_hint_request_body, question_retry_hint_response)

        # -------------------- Question Retry Hint Media Creation -------------------- #
        question_retry_hint_media_request_body = {
            "question_retry_hint": question_retry_hint_response["id"],
            "media": self.question_retry_hint_file,
        }
        question_retry_hint_media_response: dict = QuestionRetryHintMediaUnitTest.do_create_question_retry_hint_media(self, question_retry_hint_media_request_body)  # type: ignore

        # ----------------------------- Question Tag Creation ---------------------------- #
        question_tag_request_body = {
            "question": question_response["id"],
            "tag": tag_response["id"],
        }
        question_tag_response: dict = QuestionTagUnitTest.do_create_question_tag(self, question_tag_request_body)  # type: ignore
        request_response_values_asserter(self, question_tag_request_body, question_tag_response)

        # -------------------- Question Attempt Response Creation -------------------- #
        question_attempt_response_request_body = {
            "question": question_response["id"],
            "text": "correct answer",
            "type": "correct",
        }
        question_attempt_response_response: dict = QuestionAttemptResponseUnitTest.do_create_question_attempt_response(self, question_attempt_response_request_body)  # type: ignore
        request_response_values_asserter(self, question_attempt_response_request_body, question_attempt_response_response)


# ?###################################################
# ?              HELPER FUNCTIONS
# ?###################################################
def request_response_values_asserter(self, request_body, response_data):
    for key in request_body:
        if key in response_data:
            if isinstance(response_data[key], dict):
                response_data[key] = response_data[key]["id"]
            self.assertEqual(response_data[key], request_body[key])


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
