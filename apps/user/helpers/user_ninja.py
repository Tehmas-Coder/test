import json

from cryptography.fernet import Fernet
from decouple import config
from django.db import transaction
from rest_framework import status
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import OrganizationUser
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.user.models import BaseUser
from apps.user.utils.utils import get_roles_names
from core.middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import get_encryption_key, make_error_response


class UserNinja:
    def __init__(self, logged_in_user, request_data: dict, serializer_class) -> None:
        self.logged_in_user: BaseUser = logged_in_user
        self.logged_in_user_roles: list = self.logged_in_user.get_user_role_slugs
        self.is_super_user: bool = self.logged_in_user.is_superuser
        self.data_dict = request_data
        self.serializer_class = serializer_class

    # ---------------------------------------------------------------------------- #
    #                                Public methods                                #
    # ---------------------------------------------------------------------------- #
    def create_user(self) -> dict:
        self.request_data_role_ids: list = self.data_dict.pop("roles", [])
        self.is_requested_role_candidate: bool = "candidate" in get_roles_names(self.request_data_role_ids)

        self.created_user_data = self.__validate_and_create_user(self.serializer_class(data=self.data_dict))
        self.__create_candidate_or_organization_user()
        self.__send_email_verification_link()
        return self.created_user_data

    @staticmethod
    def set_role(user, roles):
        if not user:
            ResponseMiddleware.return_now(make_error_response(message="User not found"))
        try:
            user.roles.set(roles)
        except Exception as e:
            ResponseMiddleware.return_now(make_error_response(message=f"Invalid Role"))

    def update_user(self, requested_user_instance: BaseUser):
        self.requested_user_instance = requested_user_instance

        self.__validate_password()
        self.__create_profile_picture_media()  # Creating the media transaction for profile picture then setting the media id in the profile_picture value in request data
        self.__validate_and_update_user(self.serializer_class(requested_user_instance, data=self.data_dict, partial=True))

    # ---------------------------------------------------------------------------- #
    #                                Private methods                               #
    # ---------------------------------------------------------------------------- #

    def __validate_and_create_user(self, serializer_instance):
        if not serializer_instance.is_valid():
            errors = serializer_instance.errors
            if "email" in serializer_instance.errors:
                errors = {"error": "User with this email already exists"}
            ResponseMiddleware.return_now(Response(errors, status=status.HTTP_400_BAD_REQUEST))
        user_instance = serializer_instance.save()
        user_instance.roles.set(self.request_data_role_ids)
        return serializer_instance.data

    def __create_candidate_or_organization_user(self):
        organization = self.data_dict.get("organization", None)
        if not self.is_super_user:
            organization = OrganizationUser.objects.filter(user_id=self.logged_in_user.id).values("organization_id").first()["organization_id"]  # type: ignore
            if "candidate" in self.logged_in_user_roles:
                transaction.set_rollback(True)
                ResponseMiddleware.return_now(make_error_response(message="Candidate is not allowed to create a user"))
        if self.is_requested_role_candidate:
            self.__create_candidate(organization)
        else:
            self.__create_organization_user(organization)

    def __create_candidate(self, organization):
        Candidate.objects.create(user_id=self.created_user_data["id"], organization_id=organization)  # type: ignore

    def __create_organization_user(self, organization):
        if organization is None:
            transaction.set_rollback(True)
            ResponseMiddleware.return_now(make_error_response(message="Organization is required for creating organization user"))
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
            ResponseMiddleware.return_now(make_error_response(message="User created successfully but failed to send email"))
        del email_notification_ninja

    def __validate_password(self):
        old_password = self.data_dict.get("old_password")
        new_password = self.data_dict.get("new_password")

        if old_password:
            if self.requested_user_instance.check_password(old_password):
                self.data_dict["password"] = new_password
            else:
                ResponseMiddleware.return_now(make_error_response(message="Old password is incorrect"))

    def __create_profile_picture_media(self):
        profile_picture = self.data_dict.get("profile_picture", None)
        if profile_picture:
            media_serializer = MediaSerializer(data={"file": profile_picture})
            media_serializer.is_valid()
            media_serializer.save()
            media_id = media_serializer.data["id"]  # type: ignore
            self.data_dict["profile_picture"] = media_id

    def __validate_and_update_user(self, serializer_instance):
        if not serializer_instance.is_valid():
            ResponseMiddleware.return_now(Response(serializer_instance.errors, status=status.HTTP_400_BAD_REQUEST))
        serializer_instance.save()
