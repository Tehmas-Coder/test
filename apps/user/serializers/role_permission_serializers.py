from rest_framework import serializers

from apps.user.models import Permission, Role, RolePermission
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


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
            "permissions",
        ] + get_base_model_fields()


class RoleDetailSerializer(BaseModelSerializer):
    role_permissions = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "slug",
            "role_permissions",
        ] + get_base_model_fields()

    def get_role_permissions(self, obj):
        # role_permissions = list(obj.role_permissions.filter(is_active=True).values())
        role_permissions = obj.role_permissions.all()
        data = RolePermissionSerializerForRole(role_permissions, many=True).data
        return data


class RolePermissionSerializerForRole(BaseModelSerializer):
    permission = PermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "is_active",
            "permission",
        ] + get_base_model_fields()


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
