import json

from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class QuestionChoiceUnitTest(TestSetUp):
    fixtures = [
        "media_type_seed",
        "question_type_seed",
        "question_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_question_choice(self, request_body):
        print_test_header("create_question_choice")
        url = "/api/question-choice/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            format="multipart",
        )
        validate_success_201_test_response(self, response)
        return response.data  # type: ignore

    def do_update_one_question_choice(self, question_choice_id, request_body):
        print_test_header("update_question_choice")
        url = f"/api/question-choice/{question_choice_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
        )
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_delete_one_question_choice(self, question_choice_id):
        print_test_header("delete_question_choice")
        url = f"/api/question-choice/{question_choice_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class QuestionChoiceTest(QuestionChoiceUnitTest):
    validation_keys = [
        "id",
        "title",
        "text",
        "weight",
        "is_negative_weight",
        "is_correct",
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
    def test_cases_question_choice(self):
        test_record_id = self.successfull_creation_of_a_record_test()
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        file_1 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
        file_2 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")

        # TODO: change the request body after fixes from frontend(bulk create api usage instead of this one)
        # request_body = {
        #     "data": json.dumps(
        #         {
        #             "question": 1,
        #             "title": "Choice 1",
        #             "text": "",
        #             "weight": 1,
        #             "is_negative_weight": 0,
        #             "is_correct": 1,
        #             "has_media": 1,
        #             "medias": ["file_1", "file_2"],
        #         }
        #     ),
        #     "file_1": file_1,
        #     "file_2": file_2,
        # }
        request_body = {
            "question": 1,
            "title": "Choice 1",
            "text": "",
            "weight": 1,
            "is_negative_weight": 0,
            "is_correct": 1,
            "has_media": 1,
            "file_1": file_1,
            "file_2": file_2,
        }

        json_data = self.do_create_question_choice(request_body)
        for key in self.validation_keys:
            self.assertIn(key, json_data)

        return json_data["id"]

    def successfull_updation_of_record_test(self, test_record_id):
        updated_request_body = {
            "title": "Choice 1232",
            "text": "Test updated",
            "is_negative_weight": 1,
        }
        updated_response_json_data = self.do_update_one_question_choice(test_record_id, updated_request_body)
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in self.validation_keys:
            self.assertIn(key, updated_response_json_data)
        for key in updated_request_body:
            self.assertEqual(updated_response_json_data[key], updated_request_body[key])

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_question_choice(test_record_id)


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
