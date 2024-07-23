from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from core.test_setup import TestSetUp
from rest_framework import status


class QuestionRetryHintUnitTest(TestSetUp):
    fixtures = [
        "media_type_seed",
        "question_type_seed",
        "question_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_question_retry_hint(self, request_body):
        print_test_header("create_question_retry_hint")
        url = "/api/question-retry-hint/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            format="multipart",
        )
        debug_print(response.data)
        validate_success_201_test_response(self, response)
        return response.data

    def do_update_one_question_retry_hint(self, question_retry_hint_id, request_body):
        print_test_header("update_question_retry_hint")
        url = f"/api/question-retry-hint/{question_retry_hint_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
        )
        debug_print(response.data)
        validate_success_200_test_response(self, response)
        return response.data

    def do_delete_one_question_retry_hint(self, question_retry_hint_id):
        print_test_header("delete_question_retry_hint")
        url = f"/api/question-retry-hint/{question_retry_hint_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class QuestionRetryHintTest(QuestionRetryHintUnitTest):
    validation_keys = [
        "id",
        "text",
        "sequence",
        "has_media",
        "medias",
        "description",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "meta_status",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_question_retry_hint(self):
        test_record_id = self.successfull_creation_of_a_record_test()
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        file_1 = open(
            "./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb"
        )
        file_2 = open(
            "./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb"
        )

        request_body = {
            "question": 1,
            "text": "This is hint number 1",
            "has_media": 1,
            "file_1": file_1,
            "file_2": file_2,
        }
        json_data = self.do_create_question_retry_hint(request_body)
        for key in self.validation_keys:
            self.assertIn(key, json_data)

        return json_data["id"]

    def successfull_updation_of_record_test(self, test_record_id):
        updated_request_body = {
            "text": "hont text updated",
            "sequence": 1,
        }
        updated_response_json_data = self.do_update_one_question_retry_hint(
            test_record_id, updated_request_body
        )
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in self.validation_keys:
            self.assertIn(key, updated_response_json_data)
        for key in updated_request_body:
            self.assertEqual(updated_response_json_data[key], updated_request_body[key])

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_question_retry_hint(test_record_id)


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
