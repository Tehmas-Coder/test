from apps.exam_public.models.exam_public_backlog_models import ExamBacklogQuestionMedia
from apps.lookups.serializers.media_serializers import MediaSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionMediaSerializer(BaseModelSerializer):
    media = MediaSerializer()

    class Meta:
        model = ExamBacklogQuestionMedia
        fields = [
            "id",
            "media",
        ] + get_base_model_fields()
