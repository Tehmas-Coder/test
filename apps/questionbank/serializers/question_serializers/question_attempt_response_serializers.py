from apps.questionbank.models import QuestionAttemptResponse
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionAttemptResponseSerializer(BaseModelSerializer):
     class Meta:
        model = QuestionAttemptResponse
        fields = [
            "id",
            "question",
            "text",
            "type",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionAttemptResponseEditSerializer(BaseModelSerializer):

    class Meta:
        model = QuestionAttemptResponse
        fields = [
            "id",
            "text",
            "type",
        ] + get_base_model_fields()
        read_only_fields = ["id"]
