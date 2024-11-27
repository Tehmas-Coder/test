from django.db import transaction
from rest_framework import serializers

from apps.questionbank.models.question_models import (
    Question,
    QuestionAttemptResponse,
    QuestionChoice,
    QuestionRetryHint,
    QuestionSubject,
    SubjectEducationLevel,
    Tag,
)
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.questionbank.serializers.question_serializers.question_attempt_response_serializers import (
    QuestionAttemptResponseSerializer,
)
from apps.questionbank.serializers.question_serializers.question_choice_serializers import (
    QuestionChoiceSerializer,
)
from apps.questionbank.serializers.question_serializers.question_media_serializers import (
    QuestionMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_retry_hint_serializers import (
    QuestionRetryHintSerializer,
)
from apps.questionbank.serializers.question_serializers.question_subject_serializers import (
    QuestionSubjectEditSerializer,
    QuestionSubjectSerializer,
)
from apps.questionbank.serializers.question_serializers.question_type_serializers import (
    QuestionTypeSerializer,
)
from apps.questionbank.serializers.tag_serializers import TagSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionSerializer(BaseModelSerializer):
    type = QuestionTypeSerializer()
    tags = TagSerializer(many=True)
    choices = QuestionChoiceSerializer(many=True, context={"source": True})
    attempt_responses = QuestionAttemptResponseSerializer(many=True, context={"exclude_question": True})
    retry_hints = QuestionRetryHintSerializer(many=True, context={"source": True})
    medias = QuestionMediaSerializer(many=True, source="questionmedia_set")
    subjects = QuestionSubjectSerializer(many=True)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "type",
            "organization",
            "text",
            "max_retries",
            "retry_penalty",
            "is_public",
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
    subjects = QuestionSubjectEditSerializer(many=True, required=False)
    tags = serializers.PrimaryKeyRelatedField(queryset=Tag.objects.all(), many=True, required=False)
    choices = QuestionChoiceSerializer(many=True, required=False, context={"exclude_question": True})
    attempt_responses = QuestionAttemptResponseSerializer(many=True, required=False, context={"exclude_question": True})
    retry_hints = QuestionRetryHintSerializer(many=True, required=False, context={"exclude_question": True})
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = [
            "id",
            "title",
            "type",
            "organization",
            "text",
            "max_retries",
            "retry_penalty",
            "is_public",
            "can_shuffle",
            "has_media",
            "subjects",
            "tags",
            "choices",
            "attempt_responses",
            "retry_hints",
            "medias",
        ]

        read_only_fields = ["id"]

    def create(self, validated_data):
        question_medias = validated_data.pop("medias", [])
        subjects_data = validated_data.pop("subjects", [])
        tags_data = validated_data.pop("tags", [])
        choices_data = validated_data.pop("choices", [])
        attempt_responses_data = validated_data.pop("attempt_responses", [])
        retry_hints_data = validated_data.pop("retry_hints", [])

        # * Create question
        question = Question.objects.create(**validated_data)

        for question_subject_data in subjects_data:
            question_subject_countries = question_subject_data.pop("countries", [])
            subject_education_level_data = question_subject_data.pop("subject_education_level")

            # * Get or create subject education level
            subject_education_level, _ = SubjectEducationLevel.objects.get_or_create(
                subject=subject_education_level_data["subject"],
                education_level=subject_education_level_data["education_level"],
                defaults=subject_education_level_data,
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
            choices_media = choice_data.pop("medias", [])
            question_choice_instance = QuestionChoice.objects.create(question=question, **choice_data)
            for media_data in choices_media:
                media_instance = MediaSerializer().create(media_data)
                question_choice_instance.medias.add(media_instance)

        # * create attempt responses
        for attempt_response_data in attempt_responses_data:
            QuestionAttemptResponse.objects.bulk_create([QuestionAttemptResponse(question=question, **attempt_response_data)])

        # * create retry hints
        for retry_hint_data in retry_hints_data:
            retry_hints_media = retry_hint_data.pop("medias", [])

            question_hint_instance = QuestionRetryHint.objects.create(question=question, **retry_hint_data)
            for media_data in retry_hints_media:
                media_instance = MediaSerializer().create(media_data)
                question_hint_instance.medias.add(media_instance)

        # * Assign tags
        question.tags.set(tags_data)

        # * Upload Media
        for media_data in question_medias:
            media_instance = MediaSerializer().create(media_data)
            question.medias.add(media_instance)

        return question

    @transaction.atomic
    def update(self, instance, validated_data):

        subjects_data = validated_data.pop("subjects", None)
        tags = validated_data.pop("tags", None)

        # * Update question
        instance.title = validated_data.get("title", instance.title)
        instance.type = validated_data.get("type", instance.type)
        instance.text = validated_data.get("text", instance.text)
        instance.max_retries = validated_data.get("max_retries", instance.max_retries)
        instance.retry_penalty = validated_data.get("retry_penalty", instance.retry_penalty)
        instance.can_shuffle = validated_data.get("can_shuffle", instance.can_shuffle)
        instance.has_media = validated_data.get("has_media", instance.has_media)
        instance.save()

        if subjects_data:
            exisiting_question_subject_ids: list = list(QuestionSubject.objects.filter(question=instance).values_list("id", flat=True))

            # * Update or create question subjects
            for question_subject_data in subjects_data:
                id = question_subject_data.pop("id", None)
                question_subject_countries = question_subject_data.pop("countries", [])
                subject_education_level_data = question_subject_data.pop("subject_education_level")

                #  Get or create subject education level
                subject_education_level, _ = SubjectEducationLevel.objects.get_or_create(
                    subject=subject_education_level_data["subject"],
                    education_level=subject_education_level_data["education_level"],
                    defaults=subject_education_level_data,
                )

                question_subject_data["subject_education_level"] = subject_education_level
                question_subject_data["question"] = instance

                #  Update Existing question subject
                if id:
                    exisiting_question_subject_ids.remove(id)
                    question_subject, _ = QuestionSubject.objects.update_or_create(pk=id, defaults=question_subject_data)
                else:
                    #  Create question subject
                    question_subject = QuestionSubject.objects.create(**question_subject_data)

                #  Assign countries to question subject, emptying countries list if the question_subject is set to global
                if question_subject_data["is_global"]:
                    question_subject.countries.set([])  # type: ignore
                else:
                    question_subject.countries.set(question_subject_countries)  # type: ignore

            # Deleting the objects which were not included in the request
            QuestionSubject.objects.filter(pk__in=exisiting_question_subject_ids).update(meta_status="deleted")

        # * Update tags
        if tags is not None:
            instance.tags.set(tags)

        #! Delete choices if question type is not single select or multiple select
        if instance.type.slug not in ["single-select", "multiple-select"]:
            QuestionChoice.objects.filter(question=instance).update(meta_status="deleted")  # Bulk Delete

        return instance
