from rest_framework import serializers

from apps.exam.models.exam_models import Section, SubSection
from apps.questionbank.models import Question
from core.serializers import BaseModelSerializer, get_base_model_fields


class SectionEditSerializer(BaseModelSerializer):
    class Meta:
        model = Section
        fields = [
            "id",
            "title",
            "sequence",
            "time_limit",
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
            "is_negative_marking",
        ] + get_base_model_fields()


class SectionSerializer(BaseModelSerializer):
    questions = serializers.PrimaryKeyRelatedField(
        queryset=Question.objects.all(), many=True, required=False
    )
    subsections = serializers.PrimaryKeyRelatedField(
        queryset=SubSection.objects.all(), many=True, required=False
    )

    class Meta:
        model = Section
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
            "is_negative_marking",
            "questions",
            "subsections",
        ] + get_base_model_fields()
