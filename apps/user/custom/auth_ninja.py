import json

from cryptography.fernet import Fernet
from django.contrib.auth import login
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.user.models.user_models import BaseUser, Role
from apps.user.serializers.user_serializers import UserSerializer
from helpers.helper_functions import get_encryption_key
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import generate_random_password, make_error_response


class AuthNinja:
    def __init__(self, exam_token, request_data) -> None:
        self.exam_token = exam_token
        self.request_data = request_data

    def register(self):
        response_data = {}
        if "is_superuser" in self.request_data:
            response_data = self.__register_superuser()
        else:
            response_data = self.__register_candidate()
        return response_data

    def exam_token_handler(self, request):
        self.response_data = {}
        decrypted_data = AuthNinja.decrypt_exam_token(self.exam_token)
        self.user = BaseUser.objects.filter(email=decrypted_data["email"]).first()
        if decrypted_data["is_public"]:
            self.__public_exam_token_handler(request, decrypted_data)
        else:
            self.response_data["route"] = "login" if self.user else "register"
        return self.response_data

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #
    def __register_superuser(self):
        try:
            self.request_data["is_verified"] = True
            super_user_instance = BaseUser.objects.create_superuser(
                email=self.request_data.pop("email"), password=self.request_data.pop("password"), **self.request_data
            )  # type:ignore
            serializer = UserSerializer(super_user_instance, context={"mutator": True})
            return serializer.data
        except Exception as e:
            ResponseMiddleware.return_now(make_error_response(message=f"{str(e)}"))

    def __register_candidate(self):
        serializer = UserSerializer(data=self.request_data, context={"mutator": False})
        if not serializer.is_valid():
            if "email" not in serializer.errors:
                ResponseMiddleware.return_now(Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST))
            user_instance = BaseUser.get_user_by_email(self.request_data["email"])
            if user_instance and user_instance.creation_context == "public_exam" and user_instance.otp:
                response_data = self.__update_already_created_user_from_public_exam(user_instance)
                ResponseMiddleware.return_now(Response(response_data, status=status.HTTP_201_CREATED))
            ResponseMiddleware.return_now(make_error_response(message="User with this email already exists"))
        user_instance = serializer.save()
        response_data = serializer.data
        # * Adding role to user
        role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
        user_instance.roles.add(role_id["id"])  # type:ignore
        # * Creating candidate instance
        if self.exam_token:
            decrypted_data = AuthNinja.decrypt_exam_token(self.exam_token)
            self.create_candidate_with_exam_token(user_instance, decrypted_data)
        else:
            Candidate.objects.create(user=user_instance)
        self.__send_otp_to_user(user_instance)
        return response_data

    def __send_otp_to_user(self, user_instance):
        if not user_instance.send_otp():
            transaction.set_rollback(True)
            ResponseMiddleware.return_now(make_error_response(message="Failed to send OTP, please try again"))

    def __update_already_created_user_from_public_exam(self, user_instance: BaseUser):
        user_instance.first_name = self.request_data.get("first_name")
        user_instance.last_name = self.request_data.get("last_name")
        user_instance.phone = self.request_data.get("phone")
        user_instance.set_password(self.request_data.get("password"))
        user_instance.creation_context = "self"
        user_instance.save()
        self.__send_otp_to_user(user_instance)
        return UserSerializer(user_instance).data

    def __public_exam_token_handler(self, request, decrypted_data):
        if not self.user:
            user_creation_required_data = self.__fetch_user_data_from_request()
            # * If any of the required data is missing, return the route to get the details
            if any(value is None for value in user_creation_required_data.values()):
                ResponseMiddleware.return_now(Response({"route": "get-details"}, status=status.HTTP_200_OK))
            self.user = BaseUser.objects.create(email=decrypted_data["email"], creation_context="public_exam", **user_creation_required_data)
            self.user.set_password(generate_random_password())
            role_id = Role.objects.filter(name__icontains="Candidate").values("id").first()
            self.user.roles.add(role_id["id"])  # type:ignore
            self.user.save()
        AuthNinja.create_candidate_with_exam_token(self.user, decrypted_data)
        login(request, self.user)
        refresh = RefreshToken.for_user(self.user)
        self.response_data["refresh"] = str(refresh)
        self.response_data["access"] = str(refresh.access_token)  # type: ignore
        self.response_data["route"] = "exam"

    def __fetch_user_data_from_request(self) -> dict:
        user_creation_required_data = {
            "first_name": self.request_data.get("first_name"),
            "last_name": self.request_data.get("last_name"),
            "country_id": self.request_data.get("country"),
        }
        return user_creation_required_data

    # ---------------------------------------------------------------------------- #
    #                                STATIC METHODS                               #
    # ---------------------------------------------------------------------------- #
    @staticmethod
    def create_candidate_with_exam_token(user_instance, decrypted_data):
        organization_id = decrypted_data["organization_id"]
        candidate_exam_id = decrypted_data["candidate_exam_id"]
        candidate_instance, _ = Candidate.objects.get_or_create(user=user_instance, organization_id=organization_id)
        CandidateExam.objects.filter(id=candidate_exam_id).update(candidate=candidate_instance)

    @staticmethod
    def decrypt_exam_token(token):
        key = get_encryption_key()
        cipher = Fernet(key)
        try:
            decrypted_data = json.loads(cipher.decrypt(token).decode())
        except:
            ResponseMiddleware.return_now(make_error_response(message="Invalid Token"))
        return decrypted_data
