from django.db import transaction
from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.user.filters.user_filter import UserFilter
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from apps.utils import get_role_name, get_user_role_detail
from utils.rna_utils import debug_print, make_error_response

from ..models import BaseUser, Role

# ---------------------------------------------------------------------------- #
#                                     USER                                     #
# ---------------------------------------------------------------------------- #


class UserViewSet(viewsets.ModelViewSet):
    queryset = BaseUser.objects.all()
    serializer_class = UserDetailSerializer
    filterset_class = UserFilter
    USER_NOT_FOUND = {"error": "User not found"}
    USER_STATUSES = ["active", "inactive", "deleted"]
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
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
        request_user_role_id = request.data.pop("role", None)
        request_user_role_name = get_role_name(request_user_role_id)

        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            if "email" in serializer.errors:
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user_instance = serializer.save()
        user_instance.roles.add(request_user_role_id)

        if logged_in_user.is_superuser:
            if request_user_role_name.lower() == "candidate":
                Candidate.objects.create(user_id=user_instance.id)

        elif logged_in_user.is_authenticated:
            logged_in_user_role_detail = get_user_role_detail(logged_in_user.id)
            if logged_in_user_role_detail["role_name"].lower() in ["admin", "administrator", "examiner"]:
                if request_user_role_name.lower() == "candidate":
                    user_organization_id = OrganizationUser.objects.filter(user_id=logged_in_user.id).values("organization").first()
                    if user_organization_id:
                        Candidate.objects.create(user_id=user_instance.id, organization_id=user_organization_id["organization"])

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object(id=kwargs.get("pk"))
        if not instance:
            return Response(self.USER_NOT_FOUND, status=404)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

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
