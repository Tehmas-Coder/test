from rest_framework import serializers

from apps.lookups.models import Country, MeasuringUnit
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.questionbank.models import DifficultyLevel, QuestionSubject
from apps.questionbank.serializers.question_serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_education_level_serializers import (
    SubjectEducationLevelEditSerializer,
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
    name = serializers.CharField(source="subject_education_level.subject.name")
    education_level = serializers.SerializerMethodField()
    countries = CountrySerializer(many=True)
    difficulty_level = DifficultyLevelSerializer()
    measuring_unit = MeasuringUnitSerializer()

    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "name",
            "question",
            "education_level",
            "difficulty_level",
            "measuring_unit",
            "countries",
            "time_limit",
            "total_marks",
            "is_optional",
            "is_global",
        ] + get_base_model_fields()

    def get_education_level(self, obj):
        return obj.subject_education_level.education_level.name


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
