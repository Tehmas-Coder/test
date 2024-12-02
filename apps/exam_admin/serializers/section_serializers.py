from apps.exam_admin.models.exam_admin_models import Section
from core.serializers import BaseModelSerializer, get_base_model_fields


class SectionEditSerializer(BaseModelSerializer):
    class Meta:
        model = Section
        fields = [
            "id",
            "exam",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()


class SectionSerializer(BaseModelSerializer):

    class Meta:
        model = Section
        fields = [
            "id",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()
