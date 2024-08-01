from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklog
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogEditSerializer(BaseModelSerializer):

    class Meta:
        model = ExamBacklog
        fields = [
            "id",
            "exam",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "education_level_name",
            "total_marks",
            "pass_marks",
            "is_global",
        ] + get_base_model_fields()
