from rest_framework import serializers

from apps.lookups.serializers.organization_serializers import OrganizationEditSerializer
from apps.user.models.user_models import Permission, Role, RolePermission
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
class RolePermissionSerializer(BaseModelSerializer):
    permission = PermissionSerializer(read_only=True)

    class Meta:
        model = RolePermission
        fields = [
            "id",
            "is_active",
            "permission",
        ] + get_base_model_fields()


class RoleSerializer(BaseModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    role_permissions = RolePermissionSerializer(many=True)
    user_count = serializers.IntegerField(required=False)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "slug",
            "is_system_role",
            "user_count",
            "organization",
            "permissions",
            "role_permissions",
        ] + get_base_model_fields()

    def __init__(self, instance=None, data=..., **kwargs):
        self._context = kwargs.get("context", {})
        if self._context.get("mutator", False):
            self.fields.pop("role_permissions")
            self.fields.pop("user_count")
        else:
            self.fields.pop("permissions")
        if data is not ...:
            super().__init__(instance, data, **kwargs)
        super().__init__(instance, **kwargs)

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if not self._context.get("mutator", False) and res.get("organization"):
            res["organization"] = OrganizationEditSerializer(instance.organization).data
        return res
