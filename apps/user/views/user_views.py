from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.organization.models.organization_models import OrganizationUser
from apps.user.filters.user_filters import UserFilterBackend
from apps.user.helpers.system_user_ninja import SystemUserNinja
from apps.user.helpers.user_ninja import UserNinja
from apps.user.helpers.verification_email_ninja import VerificationEmailNinja
from apps.user.models import UserRole
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from apps.user.utils.utils import get_current_user_organization
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
        user_ninja_instance = UserNinja(request.user, request.data, self.get_serializer_class())
        response_data = user_ninja_instance.create()
        return Response(
            {"status": "success", "message": "User created successfully.", "data": response_data},
            status=status.HTTP_201_CREATED,
        )

    def partial_update(self, request, *args, **kwargs):
        request_data = request.data.dict()
        request_data["requested_instance"] = self.get_object()
        user_ninja_instance = UserNinja(request.user, request_data, self.get_serializer_class())
        user_ninja_instance.update()
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
        verification_ninja_instance.send(encrypted_email_token)
        return make_success_response(message="User verified successfully.")

    def resend_verification_link(self, request):
        user_email = request.data["email"]
        verification_ninja_instance = VerificationEmailNinja()
        verification_ninja_instance.resend(user_email)
        return make_success_response(message="Verification link sent successfully.")


class CreateSystemUserAPI(viewsets.ViewSet):

    @transaction.atomic
    def user_creation_by_system_user(self, request):
        logged_in_user = request.user
        logged_in_user_roles = logged_in_user.get_user_role_slugs

        if "system" not in logged_in_user_roles:
            return Response(
                {"status": "failed", "message": "User must be a system user to perform this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        request_data = request.data

        # Collect all role slugs and role names
        role_slugs = [f"{get_current_user_organization()}-{one_dict['Slug']}" for one_dict in request_data]
        slug_to_role_name = {f"{get_current_user_organization()}-{one_dict['Slug']}": one_dict["RoleName"] for one_dict in request_data}

        # Check if system roles are already created
        roles = Role.objects.filter(slug__in=role_slugs, is_system_role=True)
        found_role_slugs = set(roles.values_list("slug", flat=True))
        missing_slugs = set(role_slugs) - found_role_slugs

        if missing_slugs:
            missing_role_names = [slug_to_role_name[slug] for slug in missing_slugs]
            return Response(
                {"status": "failed", "message": f"These roles are not created in QB yet: {', '.join(missing_role_names)}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create a mapping from role slug to role id
        role_slug_id_hashmap = {role.slug: role.id for role in roles}  # type: ignore

        # Collect all emails
        emails = [one_user["Email"] for one_user in request_data]

        # Fetch existing users and organization users
        existing_users = BaseUser.objects.filter(email__in=emails)
        existing_users_dict = {user.email: user for user in existing_users}

        organization_users = OrganizationUser.objects.filter(user__email__in=emails).select_related("user")
        organization_users_dict = {org_user.user.email: org_user for org_user in organization_users}

        unentertained_emails = []

        for one_user in request_data:
            role_slug = f"{get_current_user_organization()}-{one_user['Slug']}"
            role_id = role_slug_id_hashmap[role_slug]
            email = one_user["Email"]
            to_delete = one_user.get("ToDelete", False)

            # Checking if the user already exists with any organization
            user_instance = existing_users_dict.get(email)
            create_organization_user = False

            if email in organization_users_dict:
                org_user = organization_users_dict[email]
                if org_user.organization_id != get_current_user_organization():  # type: ignore
                    unentertained_emails.append(email)
                    continue
            else:
                create_organization_user = True

            if not user_instance:
                user_instance = BaseUser.objects.create(
                    email=email,
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
                if to_delete:
                    UserRole.objects.filter(user=user_instance, role_id=role_id).update(meta_status="deleted")
                else:
                    UserRole.objects.get_or_create(
                        user=user_instance,
                        role_id=role_id,
                        defaults={"user": user_instance, "role_id": role_id},
                    )

            if create_organization_user:
                OrganizationUser.objects.create(
                    user=user_instance,
                    organization_id=get_current_user_organization(),
                )

        return Response({"data": unentertained_emails}, status=status.HTTP_200_OK)

    # @transaction.atomic
    # def user_creation_by_system_user(self, request):
    #     system_user_ninja = SystemUserNinja(request.user, request.data)
    #     return system_user_ninja.create_system_user()
