from apps.questionbank.models import QuestionType
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionTypeSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionType
        fields = ["id", "name", "slug", "abbreviation"] + get_base_model_fields()
