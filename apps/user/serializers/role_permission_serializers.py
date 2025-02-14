from rest_framework import serializers

from apps.lookups.serializers.organization_serializers import OrganizationSerializer
from apps.user.helpers.role_permission_helpers import (
    get_candidate_self_preparation_permission,
)
from apps.user.models.user_models import Permission, Role, RolePermission
from apps.user.utils.user_utils import get_current_user_candidates
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


# -------------------------------- PERMISSIONS ------------------------------- #
class PermissionSerializer(BaseModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "context_value",
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

    def __init__(self, *args, **kwargs):
        self._context: dict = kwargs.get("context", {})
        if self._context.get("mutator", False):
            self.fields.pop("role_permissions")
            self.fields.pop("user_count")
        else:
            self.fields.pop("permissions")
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        res = super().to_representation(instance)
        if res["slug"] == "candidate" and not self._context.get("mutator", False):
            candidate_instances = get_current_user_candidates()
            if candidate_instances and any(
                candidate_instance for candidate_instance in candidate_instances if candidate_instance.is_self_preparation_allowed
            ):
                res["role_permissions"].append(get_candidate_self_preparation_permission())
        if not self._context.get("mutator", False) and res.get("organization"):
            res["organization"] = OrganizationSerializer(instance.organization, context={"mutator": True}).data
        return res
