from rest_framework import serializers

from apps.lookups.models.lookup_models import Country, MeasuringUnit
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.questionbank.models.question_models import DifficultyLevel, QuestionSubject
from apps.questionbank.serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelSerializer,
)
from apps.questionbank.serializers.subject_serializers import SubjectSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionSubjectSerializer(BaseModelSerializer):

    class Meta:
        model = QuestionSubject
        fields = [
            "id",
            "subject_education_level",
            "question",
            "difficulty_level",
            "measuring_unit",
            "countries",
            "time_limit",
            "total_marks",
            "is_optional",
            "is_global",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def __init__(self, *args, **kwargs):
        self._context = kwargs.get("context", {})
        if self._context.get("mutator", False):
            self.fields.pop("question")
            self.fields["id"] = serializers.IntegerField(required=False)  # Make id optional
            self.fields["subject_education_level"] = SubjectEducationLevelSerializer(context={"mutator": True})
            self.fields["difficulty_level"] = serializers.PrimaryKeyRelatedField(queryset=DifficultyLevel.objects.all())
            self.fields["measuring_unit"] = serializers.PrimaryKeyRelatedField(queryset=MeasuringUnit.objects.all())
            self.fields["countries"] = serializers.PrimaryKeyRelatedField(queryset=Country.objects.all(), many=True, required=False)
        else:
            self.fields.pop("subject_education_level")
            self.fields["education_level"] = EducationLevelSerializer(source="subject_education_level.education_level")
            self.fields["subject"] = SubjectSerializer(source="subject_education_level.subject")
            self.fields["countries"] = CountrySerializer(many=True)
            self.fields["difficulty_level"] = DifficultyLevelSerializer()
            self.fields["measuring_unit"] = MeasuringUnitSerializer()
        super().__init__(*args, **kwargs)
