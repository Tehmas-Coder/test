from apps.exam_public.models.exam_public_backlog_models import SubSectionBacklog
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionBacklogSerializer(BaseModelSerializer):
    measuring_unit = MeasuringUnitSerializer()

    class Meta:
        model = SubSectionBacklog
        fields = [
            "id",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()
