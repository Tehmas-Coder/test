import copy
import json
from urllib import response

from rest_framework import status

from apps.organization.models.organization_models import Organization
from apps.user.models import BaseUser
from core.test_setup import TestSetUp
from utils.rna_utils import (
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class OrganizationUserUnitTest(TestSetUp):
    fixtures = ["country_test_seed", "organization_seed", "role_seed", "test_user_seed", "organization_user_seed"]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_assign_organization_user(self, request_body):
        print_test_header("assign_organization_user")
        url = "/api/organizations/assign-organization-user/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        return response

    def do_get_one_organization_users_list(self, organization_id):
        print_test_header("get_one_organization_users_list")
        url = f"/api/get-organization-users-list/{organization_id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_get_one_user_organizations_list(self):
        print_test_header("get_one_user_organizations_list")
        url = "/api/get-user-organizations-list/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data

    def do_remove_one_organization_user(self, organization_user_id):
        print_test_header("remove_organization_user")
        url = f"/api/remove-organization-user/{organization_user_id}/"
        response = self.client.delete(url, headers=self.headers)
        validate_success_204_test_response(self, response)


class OrganizationUserTest(OrganizationUserUnitTest):
    # * These are defined here so these can be accessed by all the functions
    reuseable_request_body = {
        "organization": 1,
        "user": 11,
    }
    list_of_fields_of_organization_user_model = [
        "id",
        "organization",
        "user",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_organization_user(self):
        test_record_id = self.successfull_assignment_of_an_organization_user_test()
        self.failed_assignment_of_an_existing_organization_user_test()
        self.successsfull_fetching_of_list_of_organization_users_test()
        self.successsfull_fetching_of_list_of_user_organizations_test()
        self.successfull_removal_of_one_organization_user_test(test_record_id)

    def successfull_assignment_of_an_organization_user_test(self):
        response = self.do_assign_organization_user(json.dumps(self.reuseable_request_body))
        validate_success_201_test_response(self, response)
        json_data = response.data
        for key in self.reuseable_request_body:
            self.assertEqual(json_data[key], self.reuseable_request_body[key])
        for one_field in self.list_of_fields_of_organization_user_model:
            self.assertIn(one_field, json_data)
        return json_data["id"]

    def failed_assignment_of_an_existing_organization_user_test(self):
        response = self.do_assign_organization_user(json.dumps(self.reuseable_request_body))
        validate_failed_400_test_response(self, response)

    def successsfull_fetching_of_list_of_organization_users_test(self):
        json_data = self.do_get_one_organization_users_list(organization_id=1)
        list_of_fields_of_organization_users = ["id", "name", "country", "organization_users_count", "organization_users"]
        for one_field in list_of_fields_of_organization_users:
            self.assertIn(one_field, json_data)

    def successsfull_fetching_of_list_of_user_organizations_test(self):
        json_data = self.do_get_one_user_organizations_list()
        list_of_fields_of_user_organizations = [
            "id",
            "user_id",
            "organization_id",
            "organization_name",
            "organization_country",
            "organization_country_name",
        ]
        for one_field in list_of_fields_of_user_organizations:
            self.assertIn(one_field, json_data)

    def successfull_removal_of_one_organization_user_test(self, test_record_id):
        self.do_remove_one_organization_user(test_record_id)


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
