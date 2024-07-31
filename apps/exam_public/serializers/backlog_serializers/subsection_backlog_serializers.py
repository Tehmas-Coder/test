from apps.exam_public.models.exam_public_backlog_models import SubSectionBacklog
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionBacklogEditSerializer(BaseModelSerializer):

    class Meta:
        model = SubSectionBacklog
        fields = [
            "id",
            "candidate_exam",
            "section",
            "subsection",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
            "is_negative_marking",
        ] + get_base_model_fields()

        read_only_fields = ["id"]
