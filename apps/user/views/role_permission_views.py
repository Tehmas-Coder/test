from django.db import transaction
from django.db.models import Prefetch
from django.utils.text import slugify
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.user.models import Permission, Role, RolePermission
from apps.user.serializers.role_permission_serializers import (
    PermissionSerializer,
    RoleDetailSerializer,
    RolePermissionSerializer,
    RoleSerializer,
)

# ---------------------------------------------------------------------------- #
#                                     ROLES                                    #
# ---------------------------------------------------------------------------- #


class RoleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post"]
    queryset = Role.objects.all().prefetch_related("permissions")
    serializer_class = RoleSerializer

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return RoleDetailSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action in ["list", "retrieve"]:
            return Role.objects.all().prefetch_related(Prefetch("role_permissions", queryset=RolePermission.objects.select_related("permission")))
        return super().get_queryset()

    def create(self, request, *args, **kwargs):
        new_role_data = super().create(request, *args, **kwargs)

        new_role_id = new_role_data.data["id"]
        permission_ids_list = list(Permission.objects.all().values_list("id", flat=True))

        new_role_instance = Role.objects.prefetch_related("permissions").get(pk=new_role_id)
        if len(permission_ids_list):
            new_role_instance.permissions.set(permission_ids_list)

        new_role_permssion_data = RoleSerializer(new_role_instance).data
        return Response(new_role_permssion_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        try:
            temp_ref = self.kwargs["pk"]
            is_id = temp_ref.isdigit()
            self.kwargs["pk"] = Role.objects.get(slug=temp_ref).pk if not is_id else temp_ref
            return super().retrieve(request, *args, **kwargs)
        except Role.DoesNotExist:
            return Response(
                {"status": "error", "message": "Role not found"},
                status=status.HTTP_400_BAD_REQUEST,
            )

    @action(detail=True, methods=["post"], url_path="set-permissions")
    def set_permissions(self, request, *args, **kwargs):
        permissions = request.data["permissions"]
        role_id = self.get_object().id

        RolePermission.objects.filter(role_id=role_id).update(is_active=False)

        if permissions:
            RolePermission.objects.filter(role_id=role_id, permission_id__in=permissions).update(is_active=True)

        return Response({"message": "Permissions set successfully"}, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #


class PermissionViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer


# ---------------------------------------------------------------------------- #
#                               ROLE PERMISSIONS                               #
# ---------------------------------------------------------------------------- #


class RolePermissionViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete", "put"]
    queryset = RolePermission.objects.all().select_related("role", "permission")
    serializer_class = RolePermissionSerializer

    def create(self, request, *args, **kwargs):
        request_data = request.data
        role = Role.objects.filter(id=request_data["role"]).first()
        role.permissions.set(request_data["permissions"])

        return Response({"message": "Permissions set successfully"}, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def update_role_permissions_from_sa_be(self, request, *args, **kwargs):
        request_data = request.data
        request_role_name = request_data["RoleName"]
        request_role_name_slug = slugify(request_role_name)
        role_instance = Role.objects.filter(slug=request_role_name_slug, name=request_role_name)

        if not len(role_instance) and len(request_data["default_qb_permissions"]):
            new_role_instance = Role.objects.create(name=request_role_name, is_system_role=True)
            permission_ids_list = list(Permission.objects.all().values_list("id", flat=True))

            if len(permission_ids_list):
                new_role_instance.permissions.set(permission_ids_list)
                request_permission_ids_list = [one_dict["id"] for one_dict in request_data["default_qb_permissions"]]
                RolePermission.objects.filter(role=new_role_instance, permission_id__in=request_permission_ids_list).update(is_active=True)

        else:
            role_instance = role_instance.first()
            RolePermission.objects.bulk_update(
                [
                    RolePermission(
                        id=one_permission["id"],
                        role=role_instance,
                        is_active=one_permission["is_active"],
                    )
                    for one_permission in request.data["qb_role_permissions"]
                ],
                fields=["is_active"],
            )

        return Response(status=status.HTTP_200_OK)

    @transaction.atomic
    def delete_role_with_permissions(self, request, *args, **kwargs):
        if (not request.user.is_superuser) and len(self.request.user.roles.all()):
            request_user_role = self.request.user.roles.first()
            if request_user_role.name.lower() == "system":  # make it system
                role_slug = request.data.get("role")
                role_instance = Role.objects.filter(slug=role_slug).first()

                if not role_instance:
                    return Response({"error": "Role not found"}, status=status.HTTP_404_NOT_FOUND)

                elif role_instance.is_system_role:
                    role_permissions = RolePermission.objects.filter(role=role_instance)
                    for role_permission in role_permissions:
                        role_permission.delete()

                    role_instance.delete()
                    return Response(status=status.HTTP_204_NO_CONTENT)

                else:
                    return Response({"error": "Requested role is not a system role"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(status=status.HTTP_400_BAD_REQUEST)
