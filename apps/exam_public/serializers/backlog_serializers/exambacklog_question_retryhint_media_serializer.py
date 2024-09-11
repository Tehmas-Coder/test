from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestionRetryHintMedia,
)
from apps.questionbank.serializers.media_serializers import MediaSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionRetryHintMediaSerializer(BaseModelSerializer):
    media = MediaSerializer()

    class Meta:
        model = ExamBacklogQuestionRetryHintMedia
        fields = [
            "id",
            "media",
        ] + get_base_model_fields()
