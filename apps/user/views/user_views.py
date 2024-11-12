from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.user.filters.user_filters import UserFilterBackend
from apps.user.helpers.system_user_ninja import SystemUserNinja
from apps.user.helpers.user_ninja import UserNinja
from apps.user.helpers.verification_email_ninja import VerificationEmailNinja
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from core.middlewares.current_user_middleware import get_current_user
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
        if "system" not in get_current_user().get_user_role_slugs:  # type: ignore
            return Response(
                {"status": "failed", "message": "User must be a system user to perform this action."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        system_user_ninja = SystemUserNinja(request.data)
        unentertained_emails = system_user_ninja.create_system_user()
        return Response({"data": unentertained_emails}, status=status.HTTP_200_OK)
