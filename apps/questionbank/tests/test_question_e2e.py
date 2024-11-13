import json

from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class QuestionUnitTest(TestSetUp):
    fixtures = [
        "timezone_test_seed",
        "currency_test_seed",
        "language_test_seed",
        "country_test_seed",
        "measuring_unit_seed",
        "media_type_seed",
        "tag_seed",
        "difficulty_level_seed",
        "education_level_seed",
        "subject_seed",
        "subject_education_level_seed",
        "question_type_seed",
        "question_seed",
        "question_subject_seed",
        "question_subject_country_seed",
        "question_retry_hint_seed",
        "question_choice_seed",
        "question_tag_seed",
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
    def do_create_question(self, request_body):
        print_test_header("create_question")
        url = "/api/questions/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            format="multipart",
        )
        validate_success_201_test_response(self, response)
        return response.data  # type: ignore

    def do_get_question_list(self):
        print_test_header("get_question_list")
        url = "/api/questions/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data["results"]  # type: ignore

    def do_get_one_question(self, question_id):
        print_test_header("get_one_question")
        url = f"/api/questions/{question_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_update_one_question(self, question_id, request_body):
        print_test_header("update_question")
        url = f"/api/questions/{question_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        return response  # type: ignore

    def do_delete_one_question(self, question_id):
        print_test_header("delete_question")
        url = f"/api/questions/{question_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class QuestionTest(QuestionUnitTest):
    # * These are defined here so these can be accessed by all the functions
    file_1 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_2 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")
    file_3 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_4 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")
    file_5 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_6 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")
    file_7 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_8 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_9 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")
    file_10 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_11 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_12 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    file_13 = open("./apps/questionbank/tests/test_data/images/test_image_2.jpeg", "rb")
    file_14 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")

    reuseable_request_body = {
        "title": "Are you crazy?",
        "text": "Please give reasons if you are crazy",
        "type": 1,
        "subjects": [
            {
                "difficulty_level": 1,
                "subject_education_level": {
                    "subject": 1,
                    "education_level": 1,
                },
                "is_global": 1,
                "measuring_unit": 1,
                "time_limit": 12,
                "total_marks": 5,
                "is_optional": 0,
            },
            {
                "difficulty_level": 1,
                "subject_education_level": {
                    "subject": 2,
                    "education_level": 1,
                },
                "countries": [
                    5,
                    75,
                ],
                "measuring_unit": 1,
                "time_limit": 10,
                "total_marks": 5,
                "is_optional": 0,
            },
        ],
        "max_retries": 2,
        "retry_penalty": 1,
        "can_shuffle": 1,
        "has_media": 0,
    }

    list_of_fields_of_question_model = [
        "id",
        "title",
        "text",
        "type",
        "subjects",
        "tags",
        "choices",
        "attempt_responses",
        "retry_hints",
        "medias",
        "max_retries",
        "retry_penalty",
        "can_shuffle",
        "has_media",
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
    def test_cases_question(self):
        self.successfull_creation_of_a_question_with_only_subject_and_question_data_test()
        self.successfull_creation_of_a_question_with_question_tag_test()
        self.successfull_creation_of_a_question_with_question_attempt_response_test()
        self.successfull_creation_of_a_question_with_question_media_test()
        self.successfull_creation_of_a_question_with_question_choice_test()
        self.successfull_creation_of_a_question_with_question_choice_media_test()
        self.successfull_creation_of_a_question_with_question_retry_hint_test()
        self.successfull_creation_of_a_question_with_question_retry_hint_media_test()
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        test_record_id = self.successsfull_fetching_of_one_record_test(list_of_records)
        self.failed_updation_of_any_other_organization_question_record_test(test_record_id)
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_question_with_only_subject_and_question_data_test(
        self,
    ):
        print_test_header("create_question_with_only_subject_and_question_data")
        json_data = self.do_create_question({"data": json.dumps(self.reuseable_request_body)})
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question tags as well
    def successfull_creation_of_a_question_with_question_tag_test(
        self,
    ):
        print_test_header("create_question_with_question_tag_data")
        self.reuseable_request_body["tags"] = [1, 2]
        json_data = self.do_create_question({"data": json.dumps(self.reuseable_request_body)})
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question attempt_response as well
    def successfull_creation_of_a_question_with_question_attempt_response_test(
        self,
    ):
        print_test_header("create_question_with_question_attempt_response_data")
        self.reuseable_request_body["attempt_responses"] = [
            {
                "text": "correct answer",
                "type": "correct",
            },
            {
                "text": "wrong answer",
                "type": "wrong",
            },
        ]
        json_data = self.do_create_question({"data": json.dumps(self.reuseable_request_body)})
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question media as well
    def successfull_creation_of_a_question_with_question_media_test(
        self,
    ):
        print_test_header("create_question_including_question_media")

        self.reuseable_request_body["medias"] = ["file_1", "file_2"]

        json_data = self.do_create_question(
            {
                "data": json.dumps(self.reuseable_request_body),
                "file_1": self.file_1,
                "file_2": self.file_2,
            }
        )
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question choice as well
    def successfull_creation_of_a_question_with_question_choice_test(
        self,
    ):
        print_test_header("create_question_including_question_choice")

        self.reuseable_request_body["choices"] = [
            {
                "title": "Choice 1",
                "text": "",
                "weight": 1,
                "is_negative_weight": 0,
                "is_correct": 1,
                "has_media": 0,
            },
            {
                "title": "Choice 1",
                "text": "",
                "weight": 1,
                "is_negative_weight": 0,
                "is_correct": 1,
                "has_media": 1,
            },
        ]

        json_data = self.do_create_question(
            {
                "data": json.dumps(self.reuseable_request_body),
                "file_1": self.file_3,
                "file_2": self.file_4,
            }
        )
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question choice media as well
    def successfull_creation_of_a_question_with_question_choice_media_test(
        self,
    ):
        print_test_header("create_question_including_question_choice_media")

        self.reuseable_request_body["choices"][1]["medias"] = ["file_3"]

        json_data = self.do_create_question(
            {
                "data": json.dumps(self.reuseable_request_body),
                "file_1": self.file_5,
                "file_2": self.file_6,
                "file_3": self.file_7,
            }
        )
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question retry hint as well
    def successfull_creation_of_a_question_with_question_retry_hint_test(
        self,
    ):
        print_test_header("create_question_including_question_retry_hint")

        self.reuseable_request_body["retry_hints"] = [
            {
                "text": "hint text 1",
                "sequence": 1,
                "has_media": 0,
            },
            {
                "text": "hint text 2",
                "sequence": 2,
                "has_media": 1,
            },
        ]

        json_data = self.do_create_question(
            {
                "data": json.dumps(self.reuseable_request_body),
                "file_1": self.file_8,
                "file_2": self.file_9,
                "file_3": self.file_10,
            }
        )
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    # * This test contains data to be test from previous test and additionally question retry hint media as well
    def successfull_creation_of_a_question_with_question_retry_hint_media_test(
        self,
    ):
        print_test_header("create_question_including_question_retry_hint_media")

        self.reuseable_request_body["retry_hints"][1]["medias"] = ["file_4"]

        json_data = self.do_create_question(
            {
                "data": json.dumps(self.reuseable_request_body),
                "file_1": self.file_11,
                "file_2": self.file_12,
                "file_3": self.file_13,
                "file_4": self.file_14,
            }
        )
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, json_data)

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_question_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_question_model in self.list_of_fields_of_question_model:
                self.assertIn(
                    one_value_from_list_of_fields_of_question_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_question_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_question_id = list_of_records[len(list_of_records) - 1]["id"]
        json_data = self.do_get_one_question(test_question_id)
        self.assertEqual(
            json_data["id"],
            test_question_id,
            f"The field id ({json_data['id']} is not equal to id ({test_question_id}) )",
        )
        return test_question_id

    # * Failed test case to check a user from any organization can not modify some other organization's question
    def failed_updation_of_any_other_organization_question_record_test(self, test_record_id):
        self.custom_login(email="haiderjutt@gmail.com", password="12345678")
        updated_request_body = {}
        updated_request_body["title"] = "Are you not crazy?"
        updated_request_body["text"] = "Please don't give reasons you are crazy for sure"
        updated_request_body["type"] = 2
        updated_request_body["max_retries"] = 0
        updated_request_body["subjects"] = [
            {
                "difficulty_level": 3,
                "subject_education_level": {
                    "subject": 3,
                    "education_level": 1,
                },
                "measuring_unit": 2,
                "time_limit": 10,
                "total_marks": 5,
                "is_optional": 0,
                "is_global": 0,
                "countries": [5],
            }
        ]
        updated_request_body["tags"] = [1]
        updated_response = self.do_update_one_question(test_record_id, json.dumps(updated_request_body))
        validate_failed_400_test_response(self, updated_response)

    def successfull_updation_of_record_test(self, test_record_id):
        self.custom_login(email="test_user@gmail.com", password="12345678")
        updated_request_body = {}
        updated_request_body["title"] = "Are you not crazy?"
        updated_request_body["text"] = "Please don't give reasons you are crazy for sure"
        updated_request_body["type"] = 2
        updated_request_body["max_retries"] = 0
        updated_request_body["subjects"] = [
            {
                "difficulty_level": 3,
                "subject_education_level": {
                    "subject": 3,
                    "education_level": 1,
                },
                "measuring_unit": 2,
                "time_limit": 10,
                "total_marks": 5,
                "is_optional": 0,
                "is_global": 0,
                "countries": [5],
            }
        ]
        updated_request_body["tags"] = [1]
        updated_response = self.do_update_one_question(test_record_id, json.dumps(updated_request_body))
        validate_success_200_test_response(self, updated_response)
        updated_response_json_data = updated_response.data  # type: ignore
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in self.list_of_fields_of_question_model:
            self.assertIn(key, updated_response_json_data)

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_question(test_record_id)


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
