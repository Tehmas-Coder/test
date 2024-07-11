from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import Question, QuestionSubject, SubjectEducationLevel
from rest_framework import serializers
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelDetailSerializer,
)
from apps.lookups.serializers.tag_serializers import TagSerializer
from apps.lookups.models import Tag
from apps.questionbank.serializers.question_subject_serializers import (
    QuestionSubjectEditSerializer,
)
from utils.rna_utils import debug_print


class QuestionDetailSerializer(BaseModelSerializer):
    subject_education_levels = SubjectEducationLevelDetailSerializer(many=True)
    tags = TagSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "subject_education_levels",
            "tags",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
        ] + get_base_model_fields()


class QuestionEditSerializer(serializers.ModelSerializer):
    question_subjects = QuestionSubjectEditSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "question_subjects",
            "tags",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
        ]

        read_only_fields = ["id"]

    def create(self, validated_data):
        debug_print(validated_data)

        question_subjects_data = validated_data.pop("question_subjects")
        tags_data = validated_data.pop("tags")
        question = Question.objects.create(**validated_data)

        for question_subject_data in question_subjects_data:
            question_subject_countries = question_subject_data.pop("countries")

            subject_education_level_data = question_subject_data.pop(
                "subject_education_level"
            )
            subject_education_level, _ = SubjectEducationLevel.objects.get_or_create(
                subject=subject_education_level_data["subject"],
                education_level=subject_education_level_data["education_level"],
            )
            question_subject = QuestionSubject.objects.create(
                question=question,
                subject_education_level=subject_education_level,
                **question_subject_data,
            )
            # question_subject.countries.set(question_subject_countries)

        question.tags.set(tags_data)
        return question
