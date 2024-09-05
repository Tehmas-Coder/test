from rest_framework import serializers

from apps.user.models import Permission, Role, RolePermission
from core.serializers import BaseModelSerializer, get_base_model_fields


# -------------------------------- PERMISSIONS ------------------------------- #
class PermissionSerializer(BaseModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
        ] + get_base_model_fields()


# ----------------------------------- ROLE ----------------------------------- #
class RoleSerializer(BaseModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "slug",
            "is_system_role",
            "permissions",
        ] + get_base_model_fields()


class RolePermissionSerializerForRole(BaseModelSerializer):
    permission = PermissionSerializer()

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "role",
            "is_active",
            "permission",
        ] + get_base_model_fields()


class RoleDetailSerializer(BaseModelSerializer):
    role_permissions = RolePermissionSerializerForRole(many=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "is_system_role",
            "slug",
            "role_permissions",
        ] + get_base_model_fields()

    # def get_role_permissions(self, obj):
    #     return RolePermissionSerializerForRole(obj.role_permissions.all(), many=True).data


# ------------------------------ ROLE PERMISSION ----------------------------- #
class RolePermissionSerializer(BaseModelSerializer):
    role = RoleSerializer(read_only=True)
    permission = PermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "is_active",
            "role",
            "permission",
        ] + get_base_model_fields()
