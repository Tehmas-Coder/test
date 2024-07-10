from rest_framework import serializers
from django.contrib.auth.models import AnonymousUser


def get_base_model_fields() -> list[str]:
    return [
        "id",
        "description",
        "created_at",
        "created_by",
        "updated_at",
        "updated_by",
        "meta_status",
    ]


class BaseModelSerializer(serializers.ModelSerializer):

    class Meta:
        abstract = True
        fields = get_base_model_fields()
        read_only_fields = (
            "id",
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

    def set_user_fields(self, data):
        request = self.context.get("request", None)

        if (
            request
            and hasattr(request, "user")
            and not isinstance(request.user, AnonymousUser)
        ):
            if not self.instance:
                data["created_by"] = request.user.full_name

            data["updated_by"] = request.user.full_name

        else:
            if not self.instance:
                data["created_by"] = "system"

            data["updated_by"] = "system"

        return data

    def validate(self, attrs):
        attrs = self.set_user_fields(attrs)
        return super().validate(attrs)
