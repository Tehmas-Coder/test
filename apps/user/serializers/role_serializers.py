from apps.user.models import Role
from apps.user.serializers.permission_serializers import PermissionSerializer
from rest_framework import serializers


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)

    class Meta:
        model = Role
        fields = [
            "id",
            "name",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "meta_status",
        ]
