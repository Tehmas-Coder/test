import json

from rest_framework import status
from rest_framework.response import Response

from apps.organization.tests.test_organization import OrganizationUnitTest
from apps.user.tests.test_user import UserUnitTest
from core.test_setup import TestSetUp
from utils.rna_utils import debug_print, print_test_failed, print_test_passed


class AdminEndToEndTest(TestSetUp):

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
            "email": "sheryar67@gmail.com",
            "first_name": "umer",
            "last_name": "sheryar",
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
