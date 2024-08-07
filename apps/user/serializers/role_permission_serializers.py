from apps.user.models import Permission, Role
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
            "permissions",
        ] + get_base_model_fields()
