from apps.questionbank.models import QuestionRetryHint
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionRetryHintEditSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionRetryHint
        fields = [
            "id",
            "text",
            "has_media",
            "sequence",
        ] + get_base_model_fields()
        read_only_fields = ["id"]
