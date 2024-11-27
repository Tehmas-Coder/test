from apps.questionbank.models.question_models import QuestionType
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionTypeSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionType
        fields = [
            "id",
            "name",
            "slug",
            "abbreviation",
        ] + get_base_model_fields()
        read_only_fields = ["id", "slug"]
