from apps.exam_public.models.exam_public_backlog_models import SectionBacklog
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class SectionBacklogSerializer(BaseModelSerializer):
    measuring_unit = MeasuringUnitSerializer()

    class Meta:
        model = SectionBacklog
        fields = [
            "id",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()
