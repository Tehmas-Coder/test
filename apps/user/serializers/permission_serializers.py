from rest_framework import serializers
from apps.user.models import Permission


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            "id",
            "name",
            "created_by",
            "updated_by",
            "created_at",
            "updated_at",
            "meta_status",
        ]
