from apps.questionbank.models.question_models import EducationLevel
from apps.user.utils.user_utils import get_current_user_organization
from core.serializers import BaseModelSerializer, get_base_model_fields
from middlewares.current_user_middleware import get_current_user


class EducationLevelSerializer(BaseModelSerializer):
    class Meta:
        model = EducationLevel
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
