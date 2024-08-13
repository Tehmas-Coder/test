from rest_framework import permissions, viewsets
from rest_framework.decorators import action

from apps.user.models import Permission, Role
from apps.user.serializers.role_permission_serializers import (
    PermissionSerializer,
    RoleSerializer,
)

# ---------------------------------------------------------------------------- #
#                                     ROLES                                    #
# ---------------------------------------------------------------------------- #


class RoleViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Role.objects.all()
    serializer_class = RoleSerializer


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #


class PermissionViewSet(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    queryset = Permission.objects.all()
    serializer_class = PermissionSerializer
