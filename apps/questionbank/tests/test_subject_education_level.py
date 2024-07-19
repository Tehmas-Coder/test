import copy, json

from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)
from apps.user.tests.test_setup import TestSetUp
from rest_framework import status


class SubjectEducationLevelUnitTest(TestSetUp):
    fixtures = [
        "education_level_seed",
        "subject_seed",
        "subject_education_level_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_subject_education_level(self, request_body):
        print_test_header("create_subject_education_level")
        url = "/api/subject-education-levels/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_201_test_response(self, response)
        return response.data

    def do_get_subject_education_level_list(self):
        print_test_header("get_subject_education_level_list")
        url = "/api/subject-education-levels/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data["results"]

    def do_get_one_subject_education_level(self, subject_education_level_id):
        print_test_header("get_one_subject_education_level")
        url = f"/api/subject-education-levels/{subject_education_level_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_update_one_subject_education_level(
        self, subject_education_level_id, request_body
    ):
        print_test_header("update_subject_education_level")
        url = f"/api/subject-education-levels/{subject_education_level_id}/"
        response = self.client.put(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        validate_success_200_test_response(self, response)
        return response.data

    def do_delete_one_subject_education_level(self, subject_education_level_id):
        print_test_header("delete_subject_education_level")
        url = f"/api/subject-education-levels/{subject_education_level_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class SubjectEducationLevelTest(SubjectEducationLevelUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "subject": 1,
        "education_level": 1,
    }
    list_of_fields_of_subject_education_level_model = [
        "id",
        "subject",
        "education_level",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_subject_education_level(self):
        self.successfull_creation_of_a_record_test()
        list_of_records = self.successsfull_fetching_of_list_of_records_test()
        test_record_id = self.successsfull_fetching_of_one_record_test(list_of_records)
        self.successfull_updation_of_record_test(test_record_id)
        self.successfull_deletion_of_a_record_test(test_record_id)

    def successfull_creation_of_a_record_test(self):
        json_data = self.do_create_subject_education_level(
            json.dumps(self.reuseable_request_body)
        )
        for key in self.reuseable_request_body:
            self.assertEqual(json_data[key], self.reuseable_request_body[key])
        for one_field in self.list_of_fields_of_subject_education_level_model:
            self.assertIn(one_field, json_data)

    def successsfull_fetching_of_list_of_records_test(self):
        json_data = self.do_get_subject_education_level_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data:
            for one_value_from_list_of_fields_of_application_form_section_field_choices_model in (self.list_of_fields_of_subject_education_level_model):
                self.assertIn(
                    one_value_from_list_of_fields_of_application_form_section_field_choices_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_application_form_section_field_choices_model} is not present in {test_dict}",
                )
        return json_data

    def successsfull_fetching_of_one_record_test(self, list_of_records):
        test_subject_education_level_id = list_of_records[len(list_of_records) - 1][
            "id"
        ]
        json_data = self.do_get_one_subject_education_level(
            test_subject_education_level_id
        )
        self.assertEqual(
            json_data["id"],
            test_subject_education_level_id,
            f"The Field ID ({json_data['id']} is not equal to id ({test_subject_education_level_id}) )",
        )
        return test_subject_education_level_id

    def successfull_updation_of_record_test(self, test_record_id):
        updated_request_body = copy.deepcopy(self.reuseable_request_body)
        updated_request_body["subject"] = 2

        updated_response_json_data = self.do_update_one_subject_education_level(
            test_record_id, json.dumps(updated_request_body)
        )
        self.assertEqual(updated_response_json_data["id"], test_record_id)
        for key in updated_request_body:
            self.assertEqual(updated_response_json_data[key], updated_request_body[key])

    # * Test to check the deletion of a record
    def successfull_deletion_of_a_record_test(self, test_record_id):
        self.do_delete_one_subject_education_level(test_record_id)


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
