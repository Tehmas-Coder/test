from apps.exam_admin.models.exam_admin_models import Schedule
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.datetime_utils import convert_any_datetime_to_utc
from utils.rna_utils import debug_print


class ScheduleSerializer(BaseModelSerializer):
    class Meta:
        model = Schedule
        fields = [
            "id",
            "title",
            "start_datetime",
            "end_datetime",
            "waiting_duration",
            "extra_duration",
            "organization",
        ] + get_base_model_fields()

    def create(self, validated_data):
        validated_data["start_datetime"] = convert_any_datetime_to_utc(validated_data["start_datetime"])
        validated_data["end_datetime"] = convert_any_datetime_to_utc(validated_data["end_datetime"])
        return super().create(validated_data)

    def update(self, instance, validated_data):
        if "start_datetime" in validated_data:
            validated_data["start_datetime"] = convert_any_datetime_to_utc(validated_data["start_datetime"])
        if "end_datetime" in validated_data:
            validated_data["end_datetime"] = convert_any_datetime_to_utc(validated_data["end_datetime"])
        return super().update(instance, validated_data)
