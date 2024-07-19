from apps.questionbank.models import EducationLevel
from core.serializers import BaseModelSerializer, get_base_model_fields


class EducationLevelSerializer(BaseModelSerializer):
    class Meta:
        model = EducationLevel
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
        ] + get_base_model_fields()
