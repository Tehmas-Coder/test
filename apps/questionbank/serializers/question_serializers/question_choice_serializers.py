from django.db import transaction
from rest_framework import serializers

from apps.questionbank.models import QuestionChoice
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.questionbank.serializers.question_serializers.question_choice_media_serializers import (
    QuestionChoiceMediaBulkCreateSerializer,
    QuestionChoiceMediaDetailSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class QuestionChoiceSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = QuestionChoice
        fields = [
            "id",
            "question",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
            "has_media",
            "medias",
        ] + get_base_model_fields()

        read_only_fields = ["id"]

    def validate(self, attrs):
        return super().validate(attrs)

    @transaction.atomic
    def create(self, validated_data):
        try:
            request = self.context.get("request")
            medias = []
            for file in request.FILES:  # type: ignore
                medias.append({"file": request.FILES[file]})  # type: ignore
        except:
            medias = validated_data.pop("medias")

        question_choice = QuestionChoice.objects.create(**validated_data)

        bulk_create_request_data = {"question_choice": question_choice.id, "medias": medias}  # type: ignore
        question_choice_media_serializer = QuestionChoiceMediaBulkCreateSerializer(data=bulk_create_request_data)
        question_choice_media_serializer.is_valid(raise_exception=True)
        question_choice_media_serializer.save()

        if medias:
            question_choice.has_media = True
            question_choice.save()

        return question_choice


class QuestionChoiceEditSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = QuestionChoice
        fields = [
            "id",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
            "has_media",
            "medias",
        ] + get_base_model_fields()

        read_only_fields = ["id"]


class QuestionChoiceDetailSerializer(BaseModelSerializer):
    medias = QuestionChoiceMediaDetailSerializer(many=True, required=False, source="questionchoicemedia_set")

    class Meta:
        model = QuestionChoice
        fields = [
            "id",
            "question",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
            "has_media",
            "medias",
        ] + get_base_model_fields()

        read_only_fields = ["id"]


class QuestionChoiceBulkCreateSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choices = serializers.ListField(child=QuestionChoiceEditSerializer())

    def validate(self, data):
        question_choice_serializer_errors = []
        self.question_choices_instances_data = []
        self.question_choices_media_hashmap = {}

        for index, choice in enumerate(data.get("choices", [])):
            question_choice_data = {"question": data.get("question"), **choice}
            question_choice_serializer = QuestionChoiceSerializer(data=question_choice_data)
            if not question_choice_serializer.is_valid():
                question_choice_serializer_errors.append(question_choice_serializer.errors)
            else:
                choice_title = question_choice_serializer.validated_data["title"]
                choices_medias = question_choice_serializer.validated_data.pop("medias", [])
                if choices_medias:
                    self.question_choices_media_hashmap[choice_title + f"_{index}"] = choices_medias
                self.question_choices_instances_data.append(question_choice_serializer.validated_data)

        if question_choice_serializer_errors:
            raise serializers.ValidationError({"question_choice_errors": question_choice_serializer_errors})

        return data

    def create(self, validated_data):
        # * Bulk Create Question Choices
        question_choices_instances = [QuestionChoice(**data) for data in self.question_choices_instances_data]
        QuestionChoice.objects.bulk_create(question_choices_instances)
        created_question_choices_instances = QuestionChoice.objects.all().order_by("-created_at")[: len(question_choices_instances)]
        created_question_choices_instances = sorted(created_question_choices_instances, key=lambda instance: instance.id)

        # * Bulk Create Question Choices Medias
        for index, one_question_choice_instance in enumerate(created_question_choices_instances):
            key = one_question_choice_instance.title + f"_{index}"
            if key in self.question_choices_media_hashmap:
                medias = [{"file": one_media["file"]} for one_media in self.question_choices_media_hashmap[key]]
                media_instances = QuestionChoiceMediaBulkCreateSerializer(data={"question_choice": one_question_choice_instance.id, "medias": medias})
                media_instances.is_valid(raise_exception=True)
                media_instances.save()

        return created_question_choices_instances
