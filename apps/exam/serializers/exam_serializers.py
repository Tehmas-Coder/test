from rest_framework import serializers

from apps.exam.models.exam_models import Exam
from apps.exam.serializers.exam_subject_serializers import ExamSubjectDetailSerializer
from apps.questionbank.models import Subject
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectListSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class ExamEditSerializer(BaseModelSerializer):
    subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), many=True, required=True
    )

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "total_marks",
            "pass_marks",
            "subjects",
            "is_global",
        ] + get_base_model_fields()


class ExamDetailSerialzer(BaseModelSerializer):
    education_level = EducationLevelSerializer()
    subjects = ExamSubjectDetailSerializer(source="examsubject_set", many=True)

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "total_marks",
            "pass_marks",
            "subjects",
            "is_global",
        ] + get_base_model_fields()
