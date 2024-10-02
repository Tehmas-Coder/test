import copy
import json

from rest_framework import status

from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class ExamUnitTest(TestSetUp):
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
        "resource_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_exam(self, request_body):
        print_test_header("create_exam")
        url = "/api/exams/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data  # type: ignore

    def do_get_exam_list(self):
        print_test_header("get_exam_list")
        url = "/api/exams/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data["results"]  # type: ignore

    def do_get_one_exam(self, exam_id):
        print_test_header("get_one_exam")
        url = f"/api/exams/{exam_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_update_one_exam(self, exam_id, request_body):
        print_test_header("update_exam")
        url = f"/api/exams/{exam_id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        return response

    def do_delete_one_exam(self, exam_id):
        print_test_header("delete_exam")
        url = f"/api/exams/{exam_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class ExamTest(ExamUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "name": "exam 3",
        "code": "E-1",
        "abbreviation": "xyz",
        "instructions": "asd",
        "education_level": 1,
        "total_marks": 100,
        "pass_marks": 63,
        "exam_status": "active",
        "is_global": 0,
        "subjects": [2, 5],
    }
    list_of_fields_of_exam_model = [
        "id",
        "name",
        "code",
        "abbreviation",
        "instructions",
        "education_level",
        "total_marks",
        "pass_marks",
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
    def test_cases_exam(self):
        self.successfull_creation_of_a_record_test()
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        test_record_id = self.successsfull_fetching_of_one_record_test(list_of_records)
        self.failed_updation_of_any_other_organization_exam_record_test(test_record_id)
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        json_data = self.do_create_exam(json.dumps(self.reuseable_request_body))
        for one_field in self.list_of_fields_of_exam_model:
            self.assertIn(one_field, json_data)
        for key in self.reuseable_request_body:
            if key == "subjects":
                continue
            if key == "education_level":
                self.assertEqual(json_data[key]["id"], self.reuseable_request_body[key])
                continue
            self.assertEqual(json_data[key], self.reuseable_request_body[key])

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_exam_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_exam_model in self.list_of_fields_of_exam_model:
                self.assertIn(
                    one_value_from_list_of_fields_of_exam_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_exam_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_exam_id = list_of_records[len(list_of_records) - 1]["id"]
        json_data = self.do_get_one_exam(test_exam_id)
        self.assertEqual(
            json_data["id"],
            test_exam_id,
            f"The field id ({json_data['id']} is not equal to id ({test_exam_id}) )",
        )
        return test_exam_id

    # * Failed test case to check a user from any organization can not modify some other organization's exam
    def failed_updation_of_any_other_organization_exam_record_test(self, test_record_id):
        self.custom_login(email="generalcandidate@gmail.com", password="12345678")
        updated_request_body = copy.deepcopy(self.reuseable_request_body)
        updated_request_body["name"] = "Exam 3 modified"
        updated_request_body["pass_marks"] = 70
        updated_response = self.do_update_one_exam(test_record_id, json.dumps(updated_request_body))
        validate_failed_400_test_response(self, updated_response)

    def successfull_updation_of_record_test(self, test_record_id):
        self.custom_login(email="test@gmail.com", password="12345678")
        updated_request_body = copy.deepcopy(self.reuseable_request_body)
        updated_request_body["name"] = "Exam 3 modified"
        updated_request_body["pass_marks"] = 70
        updated_response = self.do_update_one_exam(test_record_id, json.dumps(updated_request_body))
        validate_success_200_test_response(self, updated_response)
        updated_response_json_data = updated_response.data  # type: ignore
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in updated_request_body:
            if key in ["name", "pass_marks"]:
                self.assertEqual(updated_response_json_data[key], updated_request_body[key])

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_exam(test_record_id)


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
