from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import (
    DifficultyLevel,
    QuestionSubject,
    SubjectEducationLevel,
)
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelEditSerializer,
)
from rest_framework import serializers
from apps.lookups.models import Country, MeasuringUnit
from utils.rna_utils import debug_print


class QuestionSubjectListSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "subject_education_level",
        ] + get_base_model_fields()


class QuestionSubjectDetailSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "question",
            "subject_education_level",
            "difficulty_level",
            "measuring_unit",
            "countries",
            "time_limit",
            "total_marks",
            "is_optional",
            "is_global",
        ] + get_base_model_fields()


class QuestionSubjectEditSerializer(BaseModelSerializer):
    subject_education_level = SubjectEducationLevelEditSerializer()
    difficulty_level = serializers.PrimaryKeyRelatedField(
        queryset=DifficultyLevel.objects.all()
    )
    measuring_unit = serializers.PrimaryKeyRelatedField(
        queryset=MeasuringUnit.objects.all()
    )
    countries = serializers.PrimaryKeyRelatedField(
        queryset=Country.objects.all(), many=True
    )

    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "subject_education_level",
            "difficulty_level",
            "measuring_unit",
            "countries",
            "time_limit",
            "total_marks",
            "is_optional",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]
