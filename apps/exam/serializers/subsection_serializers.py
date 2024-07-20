from rest_framework import serializers

from apps.exam.models.exam_models import SubSection
from apps.questionbank.models import Question
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionEditSerializer(BaseModelSerializer):
    class Meta:
        model = SubSection
        fields = [
            "id",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
        ] + get_base_model_fields()


class SubSectionSerializer(BaseModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), many=True, required=False
    )

    class Meta:
        model = SubSection
        fields = [
            "id",
            "title",
            "slug",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
            "questions",
        ] + get_base_model_fields()
