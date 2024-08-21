from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.user.models import Permission, Role, RolePermission
from apps.user.serializers.role_permission_serializers import (
    PermissionSerializer,
    RolePermissionSerializer,
    RoleSerializer,
)
from utils.rna_utils import debug_print, make_error_response

# ---------------------------------------------------------------------------- #
#                                     ROLES                                    #
# ---------------------------------------------------------------------------- #


class RoleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post"]
    queryset = Role.objects.all().prefetch_related("permissions")
    serializer_class = RoleSerializer

    def create(self, request, *args, **kwargs):
        new_role_data = super().create(request, *args, **kwargs)
        new_role_id = new_role_data.data["id"]

        if new_role_id:
            permission_list = list(Permission.objects.all().values())

            if len(permission_list):
                RolePermission.objects.bulk_create(
                    [
                        RolePermission(
                            role_id=new_role_id,
                            permission_id=one_permission["id"],
                        )
                        for one_permission in permission_list
                    ]
                )

            new_role_instance = Role.objects.prefetch_related("permissions").get(pk=new_role_id)
            new_role_permssion_data = RoleSerializer(new_role_instance).data
            return Response(data=new_role_permssion_data, status=status.HTTP_201_CREATED)
        else:
            return Response(
                {
                    "status": "failed",
                    "message": "Role does not exist",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

    # def list(self, request, *args, **kwargs):
    #     user_role = request.user.roles.first()
    #     if request.user.is_superuser or user_role.name.lower() == "system":
    #         return super().list(request, *args, **kwargs)
    #     elif user_role:
    #         roles = self.get_queryset().filter(id__gt=user_role.id).exclude(name="System")
    #         data = RoleSerializer(roles, many=True).data
    #     else:
    #         data = None

    #     return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="set-permissions")
    def set_permissions(self, request, *args, **kwargs):
        role = self.get_object()
        try:
            role.permissions.set(request.data["permissions"])
        except Exception as e:
            return make_error_response(message=f"Invalid Permissions")

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
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = RolePermission.objects.all().select_related("role", "permission")
    serializer_class = RolePermissionSerializer

    def create(self, request, *args, **kwargs):
        request_data = request.data
        role = Role.objects.filter(id=request_data["role"]).first()
        role.permissions.set(request_data["permissions"])

        return Response({"message": "Permissions set successfully"}, status=status.HTTP_201_CREATED)
