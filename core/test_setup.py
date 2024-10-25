import json

from rest_framework import status
from rest_framework.test import APITestCase

from apps.user.models import BaseUser
from apps.user.serializers.user_serializers import UserEditSerializer


class TestSetUp(APITestCase):
    fixtures = []

    def setUp(self):
        self.tokens = None
        self.headers = {"Authorization": ""}
        self.user = None
        self.admin_user = {
            "email": "test_user@gmail.com",
            "first_name": "haider",
            "last_name": "majeed",
            "date_of_birth": "1995-07-27",
            "password": "12345678",
            "is_superuser": True,
        }

        if not BaseUser.objects.filter(email=self.admin_user["email"]).exists():
            self.custom_login(create_user=1, is_superuser=1)
        else:
            self.custom_login()
        return super().setUp()

    def custom_login(self, email=None, password=None, create_user=0, is_superuser=0):
        if create_user:
            user_serializer = UserEditSerializer(data=self.admin_user)
            user_serializer.is_valid(raise_exception=True)
            new_user_email = user_serializer.save()
            new_user_instance = BaseUser.objects.get(email=new_user_email)
            new_user_instance.__dict__["is_verified"] = True
            new_user_instance.__dict__["is_superuser"] = bool(is_superuser)
            new_user_instance.save()
            self.user = new_user_instance

        if email:
            self.user = BaseUser.objects.get(email=email)

        url = "/api/login/"
        login_request_data = {
            "email": self.admin_user["email"] if not email else email,
            "password": self.admin_user["password"] if not password else password,
        }
        response = self.client.post(url, data=json.dumps(login_request_data), content_type="application/json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.headers["Authorization"] = f"Bearer {response.data['access']}"  # type: ignore
        self.tokens = response.data["refresh"]  # type: ignore
