from apps.questionbank.models import Subject
from apps.user.utils.utils import get_current_user_organization
from core.middlewares.current_user_middleware import get_current_user
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubjectSerializer(BaseModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "organization",
        ] + get_base_model_fields()

    def create(self, validated_data):
        if not get_current_user().is_superuser:  # type: ignore
            validated_data["organization_id"] = get_current_user_organization()
        return super().create(validated_data)
