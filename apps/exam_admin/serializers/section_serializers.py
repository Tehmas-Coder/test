from rest_framework import serializers

from apps.exam_admin.models.exam_models import Section, SubSection
from apps.exam_admin.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionDetailSerializer,
)
from apps.exam_admin.serializers.subsection_serializers import SubSectionSerializer
from apps.questionbank.models import Question
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionSerializer,
)
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
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
            "is_negative_marking",
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
            "total_marks",
            "passing_marks",
            "is_global",
            "is_shuffle",
            "is_negative_marking",
        ] + get_base_model_fields()
