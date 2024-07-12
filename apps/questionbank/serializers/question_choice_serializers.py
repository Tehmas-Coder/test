from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionChoice


class QuestionChoiceEditSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionChoice
        fields = [
            "id",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
            "has_media",
        ] + get_base_model_fields()
        read_only_fields = ["id"]
