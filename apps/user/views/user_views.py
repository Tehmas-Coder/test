from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.organization.models.organization_models import OrganizationUser
from apps.user.filters.user_filters import UserFilterBackend
from apps.user.helpers.user_ninja import UserNinja
from apps.user.helpers.verification_email import VerificationEmailNinja
from apps.user.models import UserRole
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from utils.rna_utils import debug_print, make_success_response

from ..models import BaseUser, Role

# ---------------------------------------------------------------------------- #
#                                     USER                                     #
# ---------------------------------------------------------------------------- #


class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True)
    serializer_class = UserDetailSerializer
    filter_backends = [UserFilterBackend]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return UserEditSerializer
        return super().get_serializer_class()

    def get_serializer_context(self):
        if self.action == "partial_update":
            return {"update_request": True}
        return super().get_serializer_context()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user_ninja_instance = UserNinja(logged_in_user=request.user, request_data=request.data, serializer_class=self.get_serializer_class())
        response_data = user_ninja_instance.create_user()
        return Response(
            {"status": "success", "message": "User created successfully.", "data": response_data},
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        user_ninja_instance = UserNinja(logged_in_user=request.user, request_data=request.data.dict(), serializer_class=self.get_serializer_class())
        user_ninja_instance.update_user(self.get_object())
        response_data = UserDetailSerializer(self.get_object()).data
        return make_success_response(data=response_data, message="User updated successfully")

    def set_user_role(self, request, *args, **kwargs):
        user = BaseUser.objects.filter(id=request.data["user"]).first()
        roles = request.data["roles"]
        UserNinja.set_role(user, roles)
        return Response({"message": "Roles set successfully"}, status=status.HTTP_200_OK)


class UserInvitaionLinkAPI(viewsets.ViewSet):
    permission_classes = [AllowAny]

    def invitaion_link(self, request):
        encrypted_email_token = request.query_params["token"]
        verification_ninja_instance = VerificationEmailNinja()
        verification_ninja_instance.send_verification_email(encrypted_email_token)
        return make_success_response(message="User verified successfully.")

    def resend_verification_link(self, request):
        user_email = request.data["email"]
        verification_ninja_instance = VerificationEmailNinja()
        verification_ninja_instance.resend_verification_link(user_email)
        return make_success_response(message="Verification link sent successfully.")


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
