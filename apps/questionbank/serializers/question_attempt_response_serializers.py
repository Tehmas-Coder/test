from apps.questionbank.models import QuestionAttemptResponse
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionAttemptResponseEditSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionAttemptResponse
        fields = [
            "id",
            "text",
            "type",
        ] + get_base_model_fields()
        read_only_fields = ["id"]
