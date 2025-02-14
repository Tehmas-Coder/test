import copy
import json

from rest_framework import status

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import OrganizationUser
from core.test_setup import TestSetUp
from utils.rna_utils import (
    color_print,
    debug_print,
    print_test_failed,
    print_test_header,
    print_test_passed,
)


class UserUnitTest(TestSetUp):
    fixtures = [
        "permission_seed",
        "resource_seed",
        "country_test_seed",
        "role_seed",
        "role_permission_seed",
        "user_seed",
        "user_role_seed",
        "organization_seed",
        "organization_user_seed",
        "media_type_seed",
    ]

    # ?###################################################
    # ?                  UNIT - TESTS
    # ?###################################################
    def do_create_user(self, request_body):
        print_test_header("create_user")
        url = "/api/users/"
        response = self.client.post(
            url,
            headers=self.headers,
            data=request_body,
            content_type="application/json",
        )
        return response

    def do_get_user_list(self):
        print_test_header("get_user_list")
        url = "/api/users/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_get_one_user(self, id):
        print_test_header("get_one_user")
        url = f"/api/users/{id}/"
        response = self.client.get(url, headers=self.headers)
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore

    def do_update_one_user(self, id, request_body):
        print_test_header("update_user")
        url = f"/api/users/{id}/"
        response = self.client.patch(
            url,
            headers=self.headers,
            data=request_body,
            format="multipart",
        )
        validate_success_200_test_response(self, response)
        return response.data  # type: ignore


class UserTest(UserUnitTest):
    # * These are defined here so these can be accessed by all the functions

    file_1 = open("./apps/questionbank/tests/test_data/images/test_image.jpeg", "rb")
    reuseable_request_body = {
        "email": "sheryarbaloch67@gmail.com",
        "first_name": "umer",
        "last_name": "sheryar",
        "password": "123456789",
        "date_of_birth": "1995-07-27",
        "country": 1,
        "phone": "+9323346489529",
        "roles": [4],
        "description": "This is a test user",
    }

    list_of_fields_of_user_model = [
        "id",
        "email",
        "first_name",
        "last_name",
        "full_name",
        "date_of_birth",
        "profile_picture",
        "roles",
        "country",
        "phone",
        "is_verified",
        "is_superuser",
        "date_joined",
        "last_login",
        "description",
    ]

    # ?###################################################
    # ?              TESTS - CASES
    # ?###################################################
    def test_cases_user(self):
        self.successful_creation_of_a_record_test()
        self.failed_creation_of_a_duplicate_record_test()
        list_of_records = self.successful_fetching_of_list_of_records_test()
        test_record_id = self.successful_fetching_of_one_record_test(list_of_records)
        self.successful_updation_of_record_test(test_record_id)

    # ?###################################################
    # ?              TESTS - FUNCTIONS
    # ?###################################################

    def successful_creation_of_a_record_test(self):
        # ------------------------ Candidate User Creation By SuperUser ------------------------ #
        response = self.do_create_user(json.dumps(self.reuseable_request_body))
        color_print("## => Testing Candidate User Creation by SuperUser")
        json_data = response.data["data"]  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in self.reuseable_request_body:
            if key == "password":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], self.reuseable_request_body[key][0])
                continue
            self.assertEqual(json_data[key], self.reuseable_request_body[key])
        validate_success_201_test_response(self, response)
        if json_data["roles"][0]["name"].lower() == "candidate":
            candidate_instance = Candidate.objects.filter(user_id=json_data["id"]).first()
            if not candidate_instance:
                color_print("Failed: User created but Candidate not created", "red")

        # ------------------------ Organization Candidate Creation By SuperUser ------------------------ #
        candidate_user_request_body = copy.deepcopy(self.reuseable_request_body)
        candidate_user_request_body["email"] = "sheryarbaloch87@gmail.com"
        candidate_user_request_body["organization"] = 2
        response = self.do_create_user(json.dumps(candidate_user_request_body))
        color_print("## => Testing Organization Candidate Creation by SuperUser")
        json_data = response.data["data"]  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in candidate_user_request_body:
            if key == "password" or key == "organization":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], candidate_user_request_body[key][0])
                continue
            self.assertEqual(json_data[key], candidate_user_request_body[key])
        validate_success_201_test_response(self, response)
        if json_data["roles"][0]["name"].lower() == "candidate":
            candidate_instance = Candidate.objects.filter(user_id=json_data["id"]).first()
            if not (candidate_instance.organization_id == candidate_user_request_body["organization"]):  # type: ignore
                color_print("Failed: User created but Candidate not created with this organization", "red")

        # ------------------------ Organization User Creation By SuperUser ------------------------ #
        request_body = copy.deepcopy(self.reuseable_request_body)
        request_body["email"] = "sheryarbaloch97@gmail.com"
        request_body["roles"] = [1, 2]
        request_body["organization"] = 2
        response = self.do_create_user(json.dumps(request_body))
        color_print("## => Testing Organization User Creation by SuperUser")
        json_data = response.data["data"]  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in request_body:
            if key == "password" or key == "organization":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], request_body[key][0])
                self.assertEqual(json_data["roles"][1]["id"], request_body[key][1])
                continue
            self.assertEqual(json_data[key], request_body[key])
        validate_success_201_test_response(self, response)
        if json_data["roles"][0]["name"].lower() != "candidate":
            organization_user_instance = OrganizationUser.objects.filter(user_id=json_data["id"]).first()
            if not organization_user_instance:
                color_print("Failed: User created but Organization user not created", "red")
                self.assertEqual(organization_user_instance.organization_id, request_body["organization"])  # type: ignore

        # -------------------- Candidate User Creation By Organization User -------------------- #
        self.custom_login(email="asgharkhan@gmail.com", password=12345678)
        request_body_for_organization_candidate = copy.deepcopy(self.reuseable_request_body)
        request_body_for_organization_candidate["email"] = "sheryarbaloch57@gmail.com"
        response = self.do_create_user(json.dumps(request_body_for_organization_candidate))
        color_print("## => Testing Candidate User Creation by OrganizationUser")
        json_data = response.data["data"]  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in request_body_for_organization_candidate:
            if key == "password":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], request_body_for_organization_candidate[key][0])
                continue
            self.assertEqual(json_data[key], request_body_for_organization_candidate[key])
        validate_success_201_test_response(self, response)
        if json_data["roles"][0]["name"].lower() == "candidate":
            user_organization = OrganizationUser.objects.filter(user_id=self.user.id).values("organization").first()  # type: ignore
            candidate_instance = Candidate.objects.filter(user_id=json_data["id"], organization_id=user_organization["organization"]).first()  # type: ignore
            if not candidate_instance:
                color_print("Failed: User created but Candidate not created", "red")

        # -------------------- Organization Worker Creation By Organization User -------------------- #
        request_body_for_organization_user = copy.deepcopy(self.reuseable_request_body)
        request_body_for_organization_user["email"] = "sheryarbaloch77@gmail.com"
        request_body_for_organization_user["roles"] = [2, 3]
        response = self.do_create_user(json.dumps(request_body_for_organization_user))
        color_print("## => Testing Organization Worker Creation by OrganizationUser")
        json_data = response.data["data"]  # type: ignore
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in request_body_for_organization_user:
            if key == "password":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], request_body_for_organization_user[key][0])
                self.assertEqual(json_data["roles"][1]["id"], request_body_for_organization_user[key][1])
                continue
            self.assertEqual(json_data[key], request_body_for_organization_user[key])
        validate_success_201_test_response(self, response)
        if json_data["roles"][0]["name"].lower() != "candidate":
            user_organization = OrganizationUser.objects.filter(user_id=self.user.id).values("organization").first()  # type: ignore
            organization_user_instance = OrganizationUser.objects.filter(
                user_id=json_data["id"], organization_id=user_organization["organization"]  # type: ignore
            ).first()
            if not organization_user_instance:
                color_print("Failed: User created but OrganizationUser not created", "red")

    def failed_creation_of_a_duplicate_record_test(self):
        response = self.do_create_user(self.reuseable_request_body)
        validate_failed_400_test_response(self, response)

    def successful_fetching_of_list_of_records_test(self):
        self.custom_login(email="test_user@gmail.com", password="12345678")
        json_data = self.do_get_user_list()
        self.assertGreater(len(json_data), 0)
        for test_dict in json_data["results"]:
            for one_value_from_list_of_fields_of_user_model in self.list_of_fields_of_user_model:
                self.assertIn(
                    one_value_from_list_of_fields_of_user_model,
                    test_dict,
                    f"The key {one_value_from_list_of_fields_of_user_model} is not present in {test_dict}",
                )
        return json_data["results"]

    def successful_fetching_of_one_record_test(self, list_of_records):
        test_user_id = list_of_records[len(list_of_records) - 5]["id"]
        json_data = self.do_get_one_user(test_user_id)
        self.assertEqual(
            json_data["id"],
            test_user_id,
            f"The field id ({json_data['id']} is not equal to id ({test_user_id}) )",
        )
        return test_user_id

    def successful_updation_of_record_test(self, test_record_id):
        updated_request_body = {}
        updated_request_body["first_name"] = "first name edited"
        updated_request_body["last_name"] = "last name edited"
        updated_request_body["profile_picture"] = self.file_1
        updated_response_json_data = self.do_update_one_user(test_record_id, updated_request_body)
        json_data = updated_response_json_data["data"]
        for one_field in self.list_of_fields_of_user_model:
            self.assertIn(one_field, json_data)
        for key in updated_request_body:
            if key == "password":
                continue
            if key == "roles":
                self.assertEqual(json_data["roles"][0]["id"], updated_request_body[key][0])
                continue
            if key == "profile_picture":
                self.assertEqual(type(json_data[key]["id"]), int)
                continue
            if key == "country":
                self.assertEqual(json_data[key]["id"], self.reuseable_request_body[key])
                continue
            self.assertEqual(json_data[key], updated_request_body[key])
        self.assertEqual(json_data["id"], test_record_id)


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
