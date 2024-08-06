from apps.exam_admin.models.exam_admin_models import Schedule
from core.serializers import BaseModelSerializer, get_base_model_fields


class ScheduleSerializer(BaseModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            "id",
            "date",
            "title",
            "start_time",
            "end_time",
            "waiting_duration",
            "extra_duration",
        ] + get_base_model_fields()
