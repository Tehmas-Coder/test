from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import (
    Question,
    QuestionChoice,
    QuestionSubject,
    SubjectEducationLevel,
)
from rest_framework import serializers
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelDetailSerializer,
)
from apps.lookups.serializers.tag_serializers import TagSerializer
from apps.lookups.models import Tag
from apps.questionbank.serializers.question_subject_serializers import (
    QuestionSubjectDetailSerializer,
    QuestionSubjectEditSerializer,
)
from utils.rna_utils import debug_print
from apps.questionbank.serializers.question_choice_serializers import (
    QuestionChoiceEditSerializer,
)


class QuestionDetailSerializer(BaseModelSerializer):
    subjects = QuestionSubjectDetailSerializer(many=True)
    tags = TagSerializer(many=True)
    choices = QuestionChoiceEditSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "subjects",
            "tags",
            "choices",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
        ] + get_base_model_fields()


class QuestionEditSerializer(serializers.ModelSerializer):
    question_subjects = QuestionSubjectEditSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True)
    choices = QuestionChoiceEditSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "question_subjects",
            "tags",
            "choices",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
        ]

        read_only_fields = ["id"]

    def create(self, validated_data):

        question_subjects_data = validated_data.pop("question_subjects")
        tags_data = validated_data.pop("tags")
        choices_data = validated_data.pop("choices", [])

        # * Create question
        question = Question.objects.create(**validated_data)

        for question_subject_data in question_subjects_data:
            question_subject_countries = question_subject_data.pop("countries")
            subject_education_level_data = question_subject_data.pop(
                "subject_education_level"
            )

            # * Get or create subject education level
            subject_education_level, _ = SubjectEducationLevel.objects.get_or_create(
                subject=subject_education_level_data["subject"],
                education_level=subject_education_level_data["education_level"],
            )

            # * Create question subject
            question_subject = QuestionSubject.objects.create(
                question=question,
                subject_education_level=subject_education_level,
                **question_subject_data,
            )

            # * Assign countries to question subject
            question_subject.countries.set(question_subject_countries)

        # * create choices
        for choice_data in choices_data:
            QuestionChoice.objects.bulk_create(
                [QuestionChoice(question=question, **choice_data)]
            )

        # * Assign tags
        question.tags.set(tags_data)
        return question
