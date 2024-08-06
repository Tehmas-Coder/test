from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestionAttemptResponse,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionAttemptResponseSerializer(BaseModelSerializer):
    class Meta:
        model = ExamBacklogQuestionAttemptResponse
        fields = [
            "id",
            "text",
            "type",
        ] + get_base_model_fields()
