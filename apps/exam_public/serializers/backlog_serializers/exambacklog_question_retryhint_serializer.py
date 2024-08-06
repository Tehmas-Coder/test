from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestionRetryHint,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_retryhint_media_serializer import (
    ExamBacklogQuestionRetryHintMediaSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionRetryHintSerializer(BaseModelSerializer):
    medias = ExamBacklogQuestionRetryHintMediaSerializer(many=True, required=False, source="exambacklogquestionretryhintmedia_set")

    class Meta:
        model = ExamBacklogQuestionRetryHint
        fields = [
            "id",
            "text",
            "sequence",
            "has_media",
            "medias",
        ] + get_base_model_fields()
        read_only_fields = ["id"]
