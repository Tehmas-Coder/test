from rest_framework import serializers

from apps.exam_admin.models.exam_admin_models import SubSection
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionEditSerializer(BaseModelSerializer):

    class Meta:
        model = SubSection
        fields = [
            "id",
            "section",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_negative_marking",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()


class SubSectionSerializer(BaseModelSerializer):

    class Meta:
        model = SubSection
        fields = [
            "id",
            "measuring_unit",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_negative_marking",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()
