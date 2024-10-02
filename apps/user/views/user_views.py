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
from apps.user.filters.user_filter import UserFilter
from apps.user.models import UserRole
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from apps.user.utils.utils import get_role_name, get_user_role_detail
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
    queryset = (
        BaseUser.objects.all()
        .select_related(
            "country",
            "profile_picture",
        )
        .prefetch_related(
            "roles",
            "roles__role_permissions",
            "roles__role_permissions__permission",
        )
    )
    serializer_class = UserDetailSerializer
    filterset_class = UserFilter
    http_method_names = ["get", "post", "patch", "delete"]
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return UserEditSerializer

        return super().get_serializer_class()

    # ------------------------------------ API ----------------------------------- #

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        logged_in_user = request.user
        request_user_role_id = request.data.pop("role", None)
        request_user_role_name = get_role_name(request_user_role_id)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if "email" in serializer.errors:
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_instance = serializer.save()
        user_instance.roles.add(request_user_role_id)
        data = serializer.data

        # * USER CREATED BY SUPER USER
        if logged_in_user.is_superuser == True:
            if request_user_role_name.lower() == "candidate":
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
            logged_in_user_role_detail = get_user_role_detail(logged_in_user.id)
            if logged_in_user_role_detail["role_name"].lower() != "candidate":
                user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user.id).values("organization").first()
                if request_user_role_name.lower() == "candidate":
                    if user_organization_id:
                        Candidate.objects.create(user_id=user_instance.id, organization_id=user_organization_id["organization"])
                else:
                    OrganizationUser.objects.create(
                        user_id=user_instance.id,
                        organization_id=user_organization_id["organization"],  # type: ignore
                    )

        key = get_encryption_key()
        cipher = Fernet(key)

        encryption_data = {"email": request.data["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())

        token_data = encrypted_email.decode("utf-8")
        qb_public_url = config("QB_PUBLIC_FE_URL", cast=str)
        qb_admin_url = config("QB_ADMIN_FE_URL", cast=str)

        if request_user_role_name.lower() == "candidate":
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
        user = serializer.save()
        response = UserDetailSerializer(user).data
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
        role = [request.data["role"]]
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        try:
            user.roles.set(role)
        except Exception as e:
            return make_error_response(message=f"Invalid Role")

        return Response({"message": "Role set successfully"}, status=status.HTTP_200_OK)


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


class ForSytemUserAPI(viewsets.ViewSet):

    @transaction.atomic
    def system_user_create(self, request, *args, **kwargs):
        logged_in_user = request.user
        logged_in_user_id = logged_in_user.id

        logged_in_user_role_data = logged_in_user.roles.values("id", "name").first()  # type: ignore
        logged_in_user_role_id = logged_in_user_role_data["id"]
        logged_in_user_role_name = logged_in_user_role_data["name"]

        if logged_in_user_role_name.lower() != "system":
            return Response(
                {"status": "failed", "message": "User in invalid"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = request.data

        # Check if sytem role is already created
        if not Role.objects.filter(slug=request_data[0]["Slug"], is_system_role=True).exists():
            return Response(
                {"status": "failed", "message": f"This role '{request_data[0]['RoleName']}' is not created in QB yet."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        logged_in_user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user_id).values("organization").first()["organization"]  # type: ignore

        created_user_role_id = Role.objects.filter(slug=request_data[0]["Slug"], name=request_data[0]["RoleName"]).values("id").first()["id"]  # type: ignore
        for one_user in request_data:
            email = one_user["Email"]
            if not BaseUser.objects.filter(email=email).exists():
                if not UserRole.objects.filter(user__email=email).exists():
                    user_instance = BaseUser.objects.create(
                        email=one_user["Email"],
                        first_name=one_user["FirstName"],
                        last_name=one_user["LastName"],
                        phone=one_user["PhoneNumber"],
                        date_of_birth=one_user["DateOfBirth"],
                    )
                    UserRole.objects.create(
                        user=user_instance,
                        role_id=created_user_role_id,
                    )

            else:
                if not UserRole.objects.filter(user__email=email).exists():
                    UserRole.objects.create(
                        user=user_instance,
                        role_id=created_user_role_id,
                    )

            if not OrganizationUser.objects.filter(
                user__email=email,
                organization_id=logged_in_user_organization_id,
            ).exists():
                OrganizationUser.objects.create(
                    user=user_instance,
                    organization_id=logged_in_user_organization_id,
                )

        return Response(status=status.HTTP_200_OK)
