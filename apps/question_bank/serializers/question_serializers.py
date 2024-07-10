from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.question_bank.models import Question


class QuestionSerializer(BaseModelSerializer):
    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "subject_education_levels",
            "tags",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
        ] + get_base_model_fields()
