from django.forms.models import model_to_dict
from rest_framework import serializers

from apps.lookups.models import Country, MeasuringUnit
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.questionbank.models import DifficultyLevel, QuestionSubject
from apps.questionbank.serializers.question_serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_education_level_serializers import (
    SubjectEducationLevelEditSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectListSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionSubjectListSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "subject_education_level",
        ] + get_base_model_fields()


class QuestionSubjectDetailSerializer(BaseModelSerializer):
    education_level = EducationLevelSerializer(
        source="subject_education_level.education_level"
    )
    subject = SubjectListSerializer(source="subject_education_level.subject")
    countries = CountrySerializer(many=True)
    difficulty_level = DifficultyLevelSerializer()
    measuring_unit = MeasuringUnitSerializer()

    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "question",
            "subject",
            "education_level",
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
        queryset=Country.objects.all(), many=True, required=False
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
            "is_global",
            "is_optional",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]
