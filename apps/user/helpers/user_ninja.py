import json

from cryptography.fernet import Fernet
from decouple import config
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import OrganizationUser
from apps.user.models import BaseUser
from apps.user.utils.utils import get_roles_names
from core.middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import get_encryption_key, make_error_response


class UserNinja:
    def __init__(self, user, request_data: dict, serializer_class) -> None:
        self.logged_in_user: BaseUser = user
        self.data_dict = request_data
        self.logged_in_user_roles: list = self.logged_in_user.get_user_role_slugs
        self.request_data_role_ids: list = self.data_dict.pop("roles", [])
        self.is_requested_role_candidate: bool = "candidate" in get_roles_names(self.request_data_role_ids)
        self.serializer_instance = serializer_class(data=self.data_dict)

    # ---------------------------------------------------------------------------- #
    #                                Public methods                                #
    # ---------------------------------------------------------------------------- #
    def create_user(self):
        self.created_user_data = self.__validate_and_save_user(self.serializer_instance)
        self.__create_candidate_or_organization_user(self.logged_in_user.is_superuser)
        self.__send_email_verification_link()
        return self.created_user_data

    @staticmethod
    def set_role(user, roles):
        if not user:
            return ResponseMiddleware.return_now(make_error_response(message="User not found"))
        try:
            user.roles.set(roles)
        except Exception as e:
            return ResponseMiddleware.return_now(make_error_response(message=f"Invalid Role"))

    # ---------------------------------------------------------------------------- #
    #                                Private methods                               #
    # ---------------------------------------------------------------------------- #

    def __validate_and_save_user(self, serializer_instance):
        if not serializer_instance.is_valid():
            errors = serializer_instance.errors
            if "email" in serializer_instance.errors:
                errors = {"error": "User with this email already exists"}
            return ResponseMiddleware.return_now(Response(errors, status=status.HTTP_400_BAD_REQUEST))
        user_instance = serializer_instance.save()
        user_instance.roles.set(self.request_data_role_ids)
        return serializer_instance.data

    def __create_candidate_or_organization_user(self, is_super_user):
        organization = self.data_dict.get("organization", None)
        if not is_super_user:
            organization = OrganizationUser.objects.filter(user_id=self.logged_in_user.id).values("organization_id").first()["organization_id"]  # type: ignore
            if "candidate" in self.logged_in_user_roles:
                transaction.set_rollback(True)
                return ResponseMiddleware.return_now(make_error_response(message="Candidate is not allowed to create a user"))
        if self.is_requested_role_candidate:
            self.__create_candidate(organization)
        else:
            self.__create_organization_user(organization)

    def __create_candidate(self, organization):
        Candidate.objects.create(user_id=self.created_user_data["id"], organization_id=organization)  # type: ignore

    def __create_organization_user(self, organization):
        if organization is None:
            transaction.set_rollback(True)
            return ResponseMiddleware.return_now(make_error_response(message="Organization is required for creating organization user"))
        OrganizationUser.objects.create(user_id=self.created_user_data["id"], organization_id=organization)  # type: ignore

    def __send_email_verification_link(self):
        key = get_encryption_key()
        cipher = Fernet(key)
        encryption_data = {"email": self.data_dict["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())
        token_data = encrypted_email.decode("utf-8")
        qb_public_url = config("QB_PUBLIC_FE_URL", cast=str)
        qb_admin_url = config("QB_ADMIN_FE_URL", cast=str)
        verification_landing_url = (
            f"{qb_public_url}verification?token={token_data}"
            if self.is_requested_role_candidate
            else f"{qb_admin_url}verification?token={token_data}"
        )
        send_email_data_dict = {
            "first_name": self.data_dict["first_name"],
            "last_name": self.data_dict["last_name"],
            "email": self.data_dict["email"],
            "password": self.data_dict["password"],
            "URL": verification_landing_url,
        }
        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_url():
            return ResponseMiddleware.return_now(make_error_response(message="User created successfully but failed to send email"))
        del email_notification_ninja
