from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import (
    Question,
    QuestionAttemptResponse,
    QuestionChoice,
    QuestionRetryHint,
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
from utils.rna_utils import color_print, debug_print
from apps.questionbank.serializers.question_choice_serializers import (
    QuestionChoiceEditSerializer,
)
from apps.questionbank.serializers.question_attempt_response_serializers import (
    QuestionAttemptResponseEditSerializer,
)
from apps.questionbank.serializers.question_retry_hint_serializers import (
    QuestionRetryHintEditSerializer,
)
from apps.questionbank.serializers.media_serializers import MediaSerializer


class QuestionDetailSerializer(BaseModelSerializer):
    subjects = QuestionSubjectDetailSerializer(many=True)
    tags = TagSerializer(many=True)
    choices = QuestionChoiceEditSerializer(many=True)
    attempt_responses = QuestionAttemptResponseEditSerializer(many=True)
    retry_hints = QuestionRetryHintEditSerializer(many=True)
    medias = MediaSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
            "subjects",
            "tags",
            "choices",
            "attempt_responses",
            "retry_hints",
            "medias",
        ] + get_base_model_fields()


class QuestionEditSerializer(serializers.ModelSerializer):
    subjects = QuestionSubjectEditSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "text",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
            "subjects",
        ]

        read_only_fields = ["id"]

    def create(self, validated_data):
        subjects_data = validated_data.pop("subjects")

        # * Create question
        question = Question.objects.create(**validated_data)

        for question_subject_data in subjects_data:
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

        return question

    def update(self, instance, validated_data):
        debug_print(validated_data)
        subjects_data = validated_data.pop("subjects")

        # * Update question
        instance.title = validated_data.get("title", instance.title)
        instance.text = validated_data.get("text", instance.text)
        instance.max_retries = validated_data.get("max_retries", instance.max_retries)
        instance.retry_penalty = validated_data.get(
            "retry_penalty", instance.retry_penalty
        )
        instance.can_shuffle = validated_data.get("can_shuffle", instance.can_shuffle)
        instance.has_media = validated_data.get("has_media", instance.has_media)
        instance.save()

        # * Update or create question subjects
        for question_subject_data in subjects_data:
            question_subject_countries = question_subject_data.pop("countries")
            subject_education_level_data = question_subject_data.pop(
                "subject_education_level"
            )

            # * Get or create subject education level
            subject_education_level, _ = SubjectEducationLevel.objects.get_or_create(
                subject=subject_education_level_data["subject"],
                education_level=subject_education_level_data["education_level"],
            )

            debug_print(subject_education_level.__dict__)

            # * Get or create question subject
            question_subject, _ = QuestionSubject.objects.get_or_create(
                question=instance,
                subject_education_level=subject_education_level,
                defaults=question_subject_data,
            )

            # * Update question subject
            question_subject.save()

            # * Assign countries to question subject
            question_subject.countries.set(question_subject_countries)

        return instance
