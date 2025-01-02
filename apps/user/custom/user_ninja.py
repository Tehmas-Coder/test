import json
from dataclasses import dataclass
from typing import Callable

from cryptography.fernet import Fernet
from decouple import config
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import OrganizationUser
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.user.models.user_models import BaseUser
from apps.user.utils.utils import get_current_user_organization, get_roles_names
from helpers.helper_functions import get_encryption_key
from middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import make_error_response


@dataclass
class UserNinja:
    logged_in_user: BaseUser
    data_dict: dict
    serializer_class: Callable

    def __post_init__(self):
        """
        This method is automatically called after the dataclass __init__ method.
        It initializes additional attributes for the UserNinja class.
        """
        self.logged_in_user_roles: list = self.logged_in_user.get_user_role_slugs
        self.is_super_user: bool = self.logged_in_user.is_superuser
        self.requested_user_instance: BaseUser = None  # type: ignore

    # ---------------------------------------------------------------------------- #
    #                                PUBLIC METHODS                                #
    # ---------------------------------------------------------------------------- #
    def create(self):
        self.request_data_role_ids: list = self.data_dict.pop("roles", [])
        self.is_requested_role_candidate: bool = "candidate" in get_roles_names(self.request_data_role_ids)
        organization = self.data_dict.get("organization", None)

        if "candidate" in self.logged_in_user_roles:
            ResponseMiddleware.return_now(make_error_response(message="Candidate is not allowed to create a user"))

        self.created_user_data = self.__validate_and_save_user()
        self.__create_candidate_or_organization_user(organization)
        self.__send_email_verification_link()
        return self.created_user_data

    def update(self):
        self.requested_user_instance: BaseUser = self.data_dict.pop("requested_instance")
        old_password = self.data_dict.get("old_password")
        new_password = self.data_dict.get("new_password")
        profile_picture = self.data_dict.get("profile_picture")

        if old_password:
            if self.__validate_password(old_password):
                self.data_dict["password"] = new_password
        if profile_picture:
            self.data_dict["profile_picture"] = self.__create_profile_picture_media(profile_picture)
        self.__validate_and_save_user(is_update=True)

    @staticmethod
    def set_role(user, roles):
        if not user:
            ResponseMiddleware.return_now(make_error_response(message="User not found"))
        try:
            user.roles.set(roles)
        except Exception as e:
            ResponseMiddleware.return_now(make_error_response(message=f"Invalid Role"))

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __validate_and_save_user(self, is_update: bool = False):
        if is_update:
            serializer_instance = self.serializer_class(self.requested_user_instance, data=self.data_dict, partial=True, context={"mutator": True})
        else:
            serializer_instance = self.serializer_class(data=self.data_dict, context={"mutator": True})

        if not serializer_instance.is_valid():
            errors = serializer_instance.errors
            if "email" in serializer_instance.errors:
                errors = {"error": "User with this email already exists"}
            ResponseMiddleware.return_now(Response(errors, status=status.HTTP_400_BAD_REQUEST))
        user_instance = serializer_instance.save()
        if not is_update:
            user_instance.roles.set(self.request_data_role_ids)
            return serializer_instance.data

    def __create_candidate_or_organization_user(self, organization):
        if not self.is_super_user:
            organization = get_current_user_organization()
        if self.is_requested_role_candidate:
            self.__create_candidate(organization, self.created_user_data["id"])  # type: ignore
        else:
            if not organization:
                transaction.set_rollback(True)
                ResponseMiddleware.return_now(make_error_response(message="Organization is required for creating organization user"))
            self.__create_organization_user(organization, self.created_user_data["id"])  # type: ignore

    def __create_candidate(self, organization, user_id):
        Candidate.objects.create(user_id=user_id, organization_id=organization)

    def __create_organization_user(self, organization, user_id):
        OrganizationUser.objects.create(user_id=user_id, organization_id=organization)

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
            ResponseMiddleware.return_now(make_error_response(message="User created successfully but failed to send email"))
        del email_notification_ninja

    def __validate_password(self, old_password) -> bool:
        if not self.requested_user_instance.check_password(old_password):  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="Old password is incorrect"))
        return True

    def __create_profile_picture_media(self, profile_picture) -> int:
        media_serializer = MediaSerializer(data={"file": profile_picture})
        media_serializer.is_valid(raise_exception=True)
        media_serializer.save()
        return media_serializer.data["id"]  # type: ignore
