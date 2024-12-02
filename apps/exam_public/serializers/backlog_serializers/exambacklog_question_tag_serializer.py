from apps.exam_public.models.exam_public_backlog_models import ExamBacklogQuestionTag
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionTagSerializer(BaseModelSerializer):
    class Meta:
        model = ExamBacklogQuestionTag
        fields = [
            "id",
            "name",
        ] + get_base_model_fields()
