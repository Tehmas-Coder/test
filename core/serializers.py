from django.contrib.auth.models import AnonymousUser
from rest_framework import serializers


def get_base_model_fields() -> list[str]:
    return [
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
            "created_at",
            "updated_at",
            "created_by",
            "updated_by",
        )

    def set_user_fields(self, data):
        request = self.context.get("request", None)

        if request and hasattr(request, "user") and not isinstance(request.user, AnonymousUser):
            if not self.instance:
                data["created_by"] = request.user

            data["updated_by"] = request.user

        else:
            if not self.instance:
                data["created_by"] = None

            data["updated_by"] = None

        return data

    def validate(self, attrs):
        attrs = self.set_user_fields(attrs)
        return super().validate(attrs)
