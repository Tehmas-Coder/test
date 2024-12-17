from django.db import transaction
from django.db.models import Count
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.lookups.custom.lookups_classes import (
    OrganizationResourceQuerysetMutator,
    OrganizationResourceValidator,
)
from apps.user.custom.role_ninja import RoleNinja
from apps.user.custom.role_permission_ninja import RolePermissionNinja
from apps.user.models.user_models import Permission, Role, RolePermission
from apps.user.serializers.role_permission_serializers import (
    PermissionSerializer,
    RoleSerializer,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from utils.rna_utils import debug_print, make_error_response

# ---------------------------------------------------------------------------- #
#                                     ROLES                                    #
# ---------------------------------------------------------------------------- #


class RoleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch"]
    queryset = Role.get_detail_queryset(permissions=True)
    serializer_class = RoleSerializer

    def get_serializer_context(self):
        if self.action in ["create", "partial_update"]:
            return {"mutator": True}
        return super().get_serializer_context()

    def get_queryset(self):
        if self.action == "retrieve":
            return Role.get_detail_queryset(organization=True, role_permissions=True, role_permissions_permission=True)
        return super().get_queryset()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if not get_current_user().is_superuser:  # type: ignore
            request.data["organization"] = get_current_user_organization()
        new_role_data = super().create(request, *args, **kwargs)
        new_role_instance = RoleNinja.add_role_permissions(new_role_data.data["id"])  # type: ignore
        response_data = RoleSerializer(new_role_instance, context={"mutator": True}).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        self.queryset = (
            Role.get_detail_queryset(organization=True, role_permissions=True, role_permissions_permission=True)
            .exclude(slug__in=["system"])
            .annotate(user_count=Count("users"))
        )
        self.queryset = OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        if "system" in get_current_user().get_user_role_slugs:  # type: ignore
            self.queryset = self.queryset.filter(is_system_role=True)
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        try:
            temp_ref = self.kwargs["pk"]
            is_id = temp_ref.isdigit()
            if not get_current_user().is_superuser:  # type: ignore
                requested_user_organization_id = get_current_user_organization()
                role_slug = slugify(f"{requested_user_organization_id}-{temp_ref}")
            else:
                role_slug = temp_ref
            self.kwargs["pk"] = Role.objects.get(slug=role_slug).pk if not is_id else temp_ref
            response_data = super().retrieve(request, *args, **kwargs).data
            if (not get_current_user().is_superuser) and response_data["organization"]:  # type: ignore
                if response_data["organization"]["id"] != requested_user_organization_id:  # type: ignore
                    return make_error_response(message="This role doesn't belong to your organization")
            return Response(response_data, status=status.HTTP_200_OK)
        except Role.DoesNotExist:
            return Response(
                {"status": "error", "message": "Role not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=["post"], url_path="set-permissions")
    def set_permissions(self, request, *args, **kwargs):
        permissions = request.data["permissions"]
        role_id = self.get_object().id
        RolePermission.objects.filter(role_id=role_id).update(is_active=False)
        RolePermission.objects.filter(role_id=role_id, permission_id__in=permissions).update(is_active=True)
        return Response({"message": "Permissions set successfully"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #


class PermissionViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer

    def list(self, request, *args, **kwargs):
        self.queryset = Permission.objects.all().exclude(context_value__in=["studentapply", "candidates"])
        return super().list(request, *args, **kwargs)


# ---------------------------------------------------------------------------- #
#                               ROLE PERMISSIONS                               #
# ---------------------------------------------------------------------------- #


class RolePermissionViewSet(viewsets.ViewSet):

    @transaction.atomic
    def update_role_permissions_from_sa_be(self, request, *args, **kwargs):
        role_permissions_ninja_instance = RolePermissionNinja(request.data)
        role_permissions_ninja_instance.update_role_permissions()
        return Response(status=status.HTTP_200_OK)

    # This api is used by student apply backend to delete a role with all its permissions
    @transaction.atomic
    def delete_role_with_permissions(self, request, *args, **kwargs):
        role_permissions_ninja_instance = RolePermissionNinja(request.data)
        role_permissions_ninja_instance.delete_role_with_its_permissions()
        return Response(status=status.HTTP_204_NO_CONTENT)
