import json

from cryptography.fernet import Fernet
from django.db import transaction
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.user.models.user_models import BaseUser, Role
from apps.user.serializers.user_serializers import UserSerializer
from helpers.helper_functions import get_encryption_key
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


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
            if "email" in serializer.errors:
                ResponseMiddleware.return_now(make_error_response(message="User with this email already exists"))
            ResponseMiddleware.return_now(Response(serializer.errors, status=400))
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
        # * Sending OTP to user
        if not user_instance.send_otp():  # type:ignore
            transaction.set_rollback(True)
            ResponseMiddleware.return_now(make_error_response(message="Failed to send OTP, please try again"))
        return response_data

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
