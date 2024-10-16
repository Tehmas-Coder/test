import json

from cryptography.fernet import Fernet
from decouple import config
from django.db import transaction
from django.forms import model_to_dict
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import OrganizationUser
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.user.filters.user_filters import UserFilterBackend
from apps.user.models import UserRole
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from apps.user.utils.utils import get_role_names
from utils.email_notifications import EmailNotification
from utils.rna_utils import (
    debug_print,
    generate_random_password,
    get_encryption_key,
    make_error_response,
)

from ..models import BaseUser, Role

# ---------------------------------------------------------------------------- #
#                                     USER                                     #
# ---------------------------------------------------------------------------- #


class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True)
    serializer_class = UserDetailSerializer
    filter_backends = [UserFilterBackend]
    http_method_names = ["get", "post", "patch", "delete"]
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return UserEditSerializer

        return super().get_serializer_class()

    def get_serializer_context(self):
        if self.action == "partial_update":
            return {"update_request": True}
        return super().get_serializer_context()

    # ------------------------------------ API ----------------------------------- #

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        logged_in_user = request.user
        logged_in_user_roles = logged_in_user.get_user_role_slugs
        request_user_role_ids = request.data.pop("roles", [])
        request_user_role_names = get_role_names(request_user_role_ids)
        is_requested_role_candidate = "candidate" in request_user_role_names

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if "email" in serializer.errors:
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_instance = serializer.save()
        user_instance.roles.set(request_user_role_ids)
        data = serializer.data

        # * USER CREATED BY SUPER USER
        if logged_in_user.is_superuser == True:
            if is_requested_role_candidate:
                organization = request.data.get("organization", None)
                Candidate.objects.create(user_id=user_instance.id, organization_id=organization)
            else:
                organization = request.data.get("organization", None)
                if organization is None:
                    transaction.set_rollback(True)
                    return make_error_response(message="Organization must be provided in order to create a user")
                OrganizationUser.objects.create(user=user_instance, organization_id=organization)

        # * USER CREATED BY ORGANIZATION USER
        else:
            if "candidate" not in logged_in_user_roles:
                user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user.id).values("organization").first()
                if is_requested_role_candidate:
                    if user_organization_id:
                        Candidate.objects.create(user_id=user_instance.id, organization_id=user_organization_id["organization"])
                else:
                    OrganizationUser.objects.create(
                        user_id=user_instance.id,
                        organization_id=user_organization_id["organization"],  # type: ignore
                    )
            else:
                transaction.set_rollback(True)
                return make_error_response(message="Candidate is not allowed to create a user")

        key = get_encryption_key()
        cipher = Fernet(key)

        encryption_data = {"email": request.data["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())

        token_data = encrypted_email.decode("utf-8")
        qb_public_url = config("QB_PUBLIC_FE_URL", cast=str)
        qb_admin_url = config("QB_ADMIN_FE_URL", cast=str)

        if is_requested_role_candidate:
            final_url = f"{qb_public_url}verification?token={token_data}"
        else:
            final_url = f"{qb_admin_url}verification?token={token_data}"

        send_email_data_dict = {
            "first_name": request.data["first_name"],
            "last_name": request.data["last_name"],
            "email": request.data["email"],
            "password": request.data["password"],
            "URL": final_url,
        }
        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_url():
            return Response(
                data={
                    "Status": "failed",
                    "message": "User created successfully and failed to sent email",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        del email_notification_ninja

        return Response(
            {
                "status": "success",
                "message": "User created successfully.",
                "data": data,
            },
            status=status.HTTP_201_CREATED,
        )

    # -------------------------------- UPDATE USER ------------------------------- #

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        request_data: dict = request.data.dict()  # type: ignore
        # * Handling password updation
        old_password = request_data.get("old_password")
        new_password = request_data.get("new_password")

        if old_password:
            if instance.check_password(old_password):
                request_data["password"] = new_password
            else:
                return make_error_response(message="Old password is incorrect")

        # * Creating the media transaction for profile picture then setting the media id in the profile_picture value
        profile_picture = request_data.get("profile_picture", None)
        if profile_picture:
            media_serializer = MediaSerializer(data={"file": profile_picture})
            media_serializer.is_valid()
            media_serializer.save()
            media_id = media_serializer.data["id"]  # type: ignore
            request_data["profile_picture"] = media_id

        serializer = self.get_serializer(instance, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = UserDetailSerializer(self.get_object()).data
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))  # type: ignore
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        instance.activate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        user_ids = request.data.get("users", [])
        users = BaseUser.objects.filter(id__in=user_ids)
        users.update(meta_status="deleted")  # Bulk Delete
        return Response({"status": "deleted", "message": "Users deleted!"})

    def set_user_role(self, request, *args, **kwargs):
        user = BaseUser.objects.filter(id=request.data["user"]).first()
        roles = request.data["roles"]
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        try:
            user.roles.set(roles)
        except Exception as e:
            return make_error_response(message=f"Invalid Role")

        return Response({"message": "Roles set successfully"}, status=status.HTTP_200_OK)


class UserInvitaionLinkAPI(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def invitaion_link(self, request):
        encrypted_email_token = request.query_params["token"]

        # * Decrypt the email
        key = get_encryption_key()
        cipher = Fernet(key)
        decrypt_user_data = cipher.decrypt(encrypted_email_token).decode()
        user_data = json.loads(decrypt_user_data)

        try:
            user_instance = BaseUser.objects.get(email=user_data["email"])

        except BaseUser.DoesNotExist:
            return Response(
                data={"Status": "failed", "message": "User does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data_dict = model_to_dict(user_instance)
        if user_data_dict["is_verified"] == True:
            return Response(
                data={"Status": "failed", "message": "User Already Verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if user_data["email"] != user_data_dict["email"]:
            return Response(
                data={"Status": "failed", "message": "Invalid Link"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_instance.is_verified = True
        user_instance.save()

        return Response(
            data={
                "Status": "success",
                "message": "User is now verified.",
            },
            status=status.HTTP_200_OK,
        )

    def resend_verification_link(self, request):
        user_email = request.data["email"]
        try:
            user_instance = BaseUser.objects.get(email=user_email)

        except BaseUser.DoesNotExist:
            return Response(
                data={"Status": "failed", "message": "User does not exist"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user_data_dict = model_to_dict(user_instance)
        if user_data_dict["is_verified"] == True:
            return Response(
                data={"Status": "failed", "message": "User Already Verified"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        new_password = generate_random_password()
        user_instance.set_password(new_password)
        user_instance.save()

        key = get_encryption_key()
        cipher = Fernet(key)

        encryption_data = {"email": user_data_dict["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())
        token_data = encrypted_email.decode("utf-8")

        url = config("QB_PUBLIC_FE_URL")
        final_url = f"{url}verification?token={token_data}"

        send_email_data_dict = {
            "first_name": user_data_dict["first_name"],
            "last_name": user_data_dict["last_name"],
            "email": user_data_dict["email"],
            "password": new_password,
            "URL": final_url,
        }

        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_url():
            return Response(
                data={
                    "Status": "failed",
                    "message": "Failed to send verification link.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        del email_notification_ninja

        return Response(
            data={
                "Status": "success",
                "message": "Verification Link Resent Successfully.",
            },
            status=status.HTTP_200_OK,
        )


class CreateSystemUserAPI(viewsets.ViewSet):

    @transaction.atomic
    def user_creation_by_system_user(self, request, *args, **kwargs):
        logged_in_user = request.user
        logged_in_user_id = logged_in_user.id
        logged_in_user_roles = logged_in_user.get_user_role_slugs

        if "system" not in logged_in_user_roles:
            return Response(
                {"status": "failed", "message": "User must be a system user to perform this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = request.data

        # Check if system roles are already created
        for one_dict in request_data:
            if not Role.objects.filter(slug=one_dict["Slug"], is_system_role=True).exists():
                return Response(
                    {"status": "failed", "message": f"This role '{one_dict['RoleName']}' is not created in QB yet."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        logged_in_user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user_id).values("organization").first()["organization"]  # type: ignore
        # Make hashmap of role_slug and role_id
        role_slug_id_hashmap = {}
        for one_dict in request_data:
            role_slug_id_hashmap[one_dict["Slug"]] = Role.objects.filter(slug=one_dict["Slug"]).values("id").first()["id"]  # type: ignore

        unentertained_emails = []
        for one_user in request_data:
            role_id = role_slug_id_hashmap[one_user["Slug"]]
            email = one_user["Email"]
            to_delete = one_user.get("ToDelete", False)

            # Checking if the user here already exist with any organization or not
            create_organization_user = False
            organization_user = OrganizationUser.objects.filter(user__email=email)
            if not organization_user.exists():
                create_organization_user = True
            elif not (organization_user.first().organization_id == logged_in_user_organization_id):  # type: ignore
                unentertained_emails.append(email)
                continue

            if not BaseUser.objects.filter(email=email).exists():
                user_instance = BaseUser.objects.create(
                    email=one_user["Email"],
                    first_name=one_user["FirstName"],
                    last_name=one_user["LastName"],
                    phone=one_user["PhoneNumber"],
                    date_of_birth=one_user["DateOfBirth"],
                )
                UserRole.objects.create(
                    user=user_instance,
                    role_id=role_id,
                )

            else:
                user_instance = BaseUser.get_user_by_email(email)
                if to_delete:
                    UserRole.objects.filter(user__email=email, role_id=role_id).update(meta_status="deleted")
                else:
                    UserRole.objects.get_or_create(
                        user=user_instance,
                        role_id=role_id,
                        defaults={"user": user_instance, "role_id": role_id},
                    )
            if create_organization_user:
                OrganizationUser.objects.create(
                    user=user_instance,
                    organization_id=logged_in_user_organization_id,
                )

        return Response({"data": unentertained_emails}, status=status.HTTP_200_OK)
