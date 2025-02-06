from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import print_test_failed, print_test_passed


class RandomExamUnitTest(TestSetUp):
    fixtures = [
        "timezone_test_seed",
        "currency_test_seed",
        "language_test_seed",
        "country_test_seed",
        "subject_seed",
        "education_level_seed",
        "subject_education_level_seed",
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


class RandomExamTest(RandomExamUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "name": "Random Test Exam",
        "code": "RET-1",
        "abbreviation": "ret1",
        "instructions": "No Instructions",
        "education_level": 1,
        "passing_percentage": 50,
        "exam_status": "draft",
        "is_global": 1,
        "subject_education_levels": [9, 10, 11, 12],
        "difficulty_levels": [1],
        "question_count": 10,
        "organization": 2,
        "is_exam_preparatory": False,
        "exam_duration": 120,
        "exam_questions_visibility": "all-at-once",
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
