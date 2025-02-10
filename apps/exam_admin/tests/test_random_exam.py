import json

from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class RandomExamUnitTest(TestSetUp):
    fixtures = [
        "tag_seed",
        "difficulty_level_seed",
        "measuring_unit_seed",
        "timezone_test_seed",
        "currency_test_seed",
        "language_test_seed",
        "country_test_seed",
        "subject_seed",
        "education_level_seed",
        "subject_education_level_seed",
        "question_type_seed",
        "question_seed",
        "question_subject_seed",
        "question_subject_country_seed",
        "question_retry_hint_seed",
        "question_choice_seed",
        "question_tag_seed",
        "exam_seed",
        "user_seed",
        "role_seed",
        "user_role_seed",
        "permission_seed",
        "resource_seed",
        "role_permission_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################

    def create_random_exam(self, request_body):
        print_test_header("create_random_exam")
        url = "/api/exams/create-random/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data  # type: ignore


class RandomExamTest(RandomExamUnitTest):
    # * These are defined here so these can be accessed by all the functions
    request_body = {
        "exam_data": {
            "name": "exam 3",
            "code": "E-3",
            "abbreviation": "xyz",
            "instructions": "asd",
            "education_level": 1,
            "passing_percentage": 50,
            "is_global": 1,
            "exam_status": "draft",
        },
        "subjects": [5, 6],
        "difficulty_levels": [1],
        "question_types": [1, 2, 3],
        "question_count": 10,
    }
    list_of_fields_of_exam_model = [
        "id",
        "name",
        "code",
        "abbreviation",
        "instructions",
        "education_level",
        "total_marks",
        "passing_percentage",
        "exam_status",
        "is_global",
        "exam_subjects",
        "questions",
        "sections",
        "description",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_random_exam(self):
        self.successfull_creation_of_a_record_test(self.request_body)

    def successfull_creation_of_a_record_test(self, request_body):
        response_data = self.create_random_exam(json.dumps(request_body))
        for field in self.list_of_fields_of_exam_model:
            self.assertIn(field, response_data.keys(), f"field '{field}' not found in response data")


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
