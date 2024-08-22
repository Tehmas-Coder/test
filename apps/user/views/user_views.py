import json

from cryptography.fernet import Fernet
from decouple import config
from django.db import transaction
from django.db.models import F
from django.forms import Media, model_to_dict
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.serializers.media_serializers import MediaSerializer
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.user.filters.user_filter import UserFilter
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from apps.utils import get_role_name, get_user_role_detail
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
    queryset = BaseUser.objects.all().select_related("country", "profile_picture").prefetch_related("roles", "roles__permissions")
    serializer_class = UserDetailSerializer
    filterset_class = UserFilter
    http_method_names = ["get", "post", "patch", "delete"]
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return UserEditSerializer

        return super().get_serializer_class()

    def get_object(self, id: int | None = None):
        try:
            return BaseUser.objects.get(pk=id or self.kwargs.get("pk"))
        except BaseUser.DoesNotExist:
            return None

    # ------------------------------------ API ----------------------------------- #

    def list(self, request, *args, **kwargs):
        self.queryset = self.queryset.filter(meta_status="active")
        return super().list(request, *args, **kwargs)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        logged_in_user = self.request.user

        # User Creation from student apply
        if (not logged_in_user.is_superuser) and len(self.request.user.roles.all()):
            request_data = request.data
            request_user_role = self.request.user.roles.first()
            if request_user_role.name.lower() == "system":  # make it system
                request_role_slug = request_data["slug"]
                request_role_name = request_data["role_name"]
                instance, _ = BaseUser.objects.get_or_create(
                    email=request_data["email"],
                    defaults={
                        "email": request_data["email"],
                        "first_name": request_data["first_name"],
                        "last_name": request_data["last_name"],
                        "phone": request_data.get("phone", None),
                        "date_of_birth": request_data.get("date_of_birth", None),
                    },
                )
                role = Role.objects.filter(name=request_role_name, slug=request_role_slug).first()
                if len(instance.roles.all()):
                    one_role = instance.roles.first()
                    if not one_role.is_system_role:
                        return Response(
                            {
                                "status": "failed",
                                "message": "User already exists and it has a role.",
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                instance.roles.add(role.id)
                data = model_to_dict(instance)
                data["roles"] = data["roles"][0].id
            else:
                request_user_role_id = request.data.pop("role", None)
                request_user_role_name = get_role_name(request_user_role_id)
                serializer = self.get_serializer(data=request.data)
                if not serializer.is_valid():
                    if "email" in serializer.errors:
                        return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

                user_instance = serializer.save()
                data = serializer.data
                user_instance.roles.add(request_user_role_id)

                logged_in_user_role_detail = get_user_role_detail(logged_in_user.id)
                if logged_in_user_role_detail["role_name"].lower() in ["admin", "administrator", "examiner"]:
                    user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user.id).values("organization").first()
                    if request_user_role_name.lower() == "candidate":
                        if user_organization_id:
                            Candidate.objects.create(user_id=user_instance.id, organization_id=user_organization_id["organization"])
                    else:
                        OrganizationUser.objects.create(
                            user_id=user_instance.id,
                            organization_id=user_organization_id["organization"],
                        )

        else:
            request_user_role_id = request.data.pop("role", None)
            request_user_role_name = get_role_name(request_user_role_id)
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                if "email" in serializer.errors:
                    return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            user_instance = serializer.save()
            data = serializer.data
            user_instance.roles.add(request_user_role_id)

            if request_user_role_name.lower() == "candidate":
                Candidate.objects.create(user_id=user_instance.id)

        key = get_encryption_key()
        cipher = Fernet(key)

        encryption_data = {"email": request.data["email"]}
        encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())

        token_data = encrypted_email.decode("utf-8")
        url = config("BASE_URL")
        final_url = f"{url}verification?token={token_data}"
        send_email_data_dict = {
            "first_name": request.data["first_name"],
            "last_name": request.data["last_name"],
            "email": request.data["email"],
            "password": request.data.get("password", ""),
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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def partial_update(self, request, *args, **kwargs):
        profile_picture = request.data.get("profile_picture", None)
        if profile_picture:
            media_serializer = MediaSerializer(data={"file": profile_picture})
            media_serializer.is_valid()
            media_serializer.save()
            media_id = media_serializer.data["id"]
            request.data["profile_picture"] = media_id

        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response({"error": "User not found"}, status=404)
        instance.deactivate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="restore")
    def restore(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        instance.activate()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete(self, request):
        user_ids = request.data.get("users", [])
        users = BaseUser.objects.filter(id__in=user_ids)
        for user in users:
            user.delete()
        return Response({"status": "deleted", "message": "Users deleted!"})


class SetUserRoleAPI(views.APIView):

    def post(self, request, *args, **kwargs):
        user = BaseUser.objects.filter(id=request.data["user"]).first()
        role = [request.data["role"]]
        if not user:
            return Response(self.USER_NOT_FOUND, status=404)
        try:
            user.roles.set(role)
        except Exception as e:
            return make_error_response(message=f"Invalid Role")

        return Response({"message": "Role set successfully"}, status=status.HTTP_200_OK)


class InvitaionLinkAPI(views.APIView):

    def get(self, request):
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


class ResendVerificationLinkAPI(views.APIView):

    def post(self, request):
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

        url = config("BASE_URL")
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
