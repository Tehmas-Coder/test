from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from core.test_setup import TestSetUp
from rest_framework import status


class QuestionTagUnitTest(TestSetUp):
    fixtures = [
        "tag_seed",
        "question_type_seed",
        "question_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_question_tag(self, request_body):
        print_test_header("create_question_tag")
        url = "/api/question-tag/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
        )
        debug_print(response.data)
        validate_success_201_test_response(self, response)
        return response.data

    def do_delete_one_question_tag(self, question_tag_id):
        print_test_header("delete_question_tag")
        url = f"/api/question-tag/{question_tag_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class QuestionTagTest(QuestionTagUnitTest):

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_question_tag(self):
        test_record_id = self.successfull_creation_of_a_record_test()
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):

        request_body = {
            "question": 1,
            "tag": 1,
        }
        json_data = self.do_create_question_tag(request_body)
        validation_keys = [
            "id",
            "question",
            "tag",
            "description",
            "created_at",
            "created_by",
            "updated_at",
            "updated_by",
            "meta_status",
        ]
        for key in validation_keys:
            self.assertIn(key, json_data)

        return json_data["id"]

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_question_tag(test_record_id)


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
