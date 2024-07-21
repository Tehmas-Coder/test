from rest_framework import serializers

from apps.exam.models.exam_models import SubSection
from apps.exam.serializers.section_subsection_serializer import (
    SectionSubSectionSerializer,
)
from apps.questionbank.models import Question
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubSectionEditSerializer(BaseModelSerializer):
    section = serializers.IntegerField(required=True, write_only=True)

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
            "section",
        ] + get_base_model_fields()

    def create(self, validated_data):
        section = validated_data.pop("section")
        subsection = super().create(validated_data)
        section_subsection_instance = SectionSubSectionSerializer(
            data={"section": section, "subsection": subsection.id}
        )
        section_subsection_instance.is_valid(raise_exception=True)
        section_subsection_instance.save()

        return subsection


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
