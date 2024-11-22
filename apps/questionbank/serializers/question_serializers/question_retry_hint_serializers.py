from rest_framework import serializers

from apps.questionbank.models.question_models import QuestionRetryHint
from apps.questionbank.serializers.media_serializers import MediaSerializer
from apps.questionbank.serializers.question_serializers.question_retry_hint_media_serializers import (
    QuestionRetryHintMediaBulkCreateSerializer,
    QuestionRetryHintMediaDetailSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionRetryHintSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = QuestionRetryHint
        fields = [
            "id",
            "question",
            "text",
            "has_media",
            "sequence",
            "medias",
        ] + get_base_model_fields()
        read_only_fields = ["id"]

    def create(self, validated_data):
        try:
            request = self.context.get("request")
            medias = []
            for file in request.FILES:  # type: ignore
                medias.append({"file": request.FILES[file]})  # type: ignore
        except:
            medias = validated_data.pop("medias")

        retry_hint = QuestionRetryHint.objects.create(**validated_data)
        for media in medias:
            media_serializer = MediaSerializer(data=media)
            media_serializer.is_valid(raise_exception=True)
            media = media_serializer.save()
            retry_hint.medias.add(media)
        retry_hint.refresh_from_db()
        return retry_hint


class QuestionRetryHintEditSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = QuestionRetryHint
        fields = [
            "id",
            "text",
            "has_media",
            "sequence",
            "medias",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionRetryHintDetailSerializer(BaseModelSerializer):
    medias = QuestionRetryHintMediaDetailSerializer(many=True, required=False, source="questionretryhintmedia_set")

    class Meta:
        model = QuestionRetryHint
        fields = [
            "id",
            "text",
            "has_media",
            "sequence",
            "medias",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionRetryHintBulkCreateSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    retry_hints = serializers.ListField(child=QuestionRetryHintEditSerializer())

    def validate(self, data):
        question_retry_hint_serializer_errors = []
        self.question_retry_hints_instances_data = []
        self.question_retry_hints_medias_hashmap = {}

        for index, retry_hint in enumerate(data.get("retry_hints", [])):
            question_retry_hint_data = {"question": data.get("question"), **retry_hint}
            question_retry_hint_serializer = QuestionRetryHintSerializer(data=question_retry_hint_data)
            if not question_retry_hint_serializer.is_valid():
                question_retry_hint_serializer_errors.append(question_retry_hint_serializer.errors)
            else:
                retry_hint_text = question_retry_hint_serializer.validated_data["text"]  # type: ignore
                retry_hint_medias = question_retry_hint_serializer.validated_data.pop("medias", [])  # type: ignore
                if retry_hint_medias:
                    self.question_retry_hints_medias_hashmap[retry_hint_text + f"_{index}"] = retry_hint_medias
                self.question_retry_hints_instances_data.append(question_retry_hint_serializer.validated_data)

        if question_retry_hint_serializer_errors:
            raise serializers.ValidationError({"question_retry_hint_errors": question_retry_hint_serializer_errors})

        return data

    def create(self, validated_data):
        # * Bulk Create Question Retry Hints
        question_retry_hints_instances = [QuestionRetryHint(**data) for data in self.question_retry_hints_instances_data]
        QuestionRetryHint.objects.bulk_create(question_retry_hints_instances)
        created_question_retry_hints_instances = QuestionRetryHint.objects.all().order_by("-created_at")[: len(question_retry_hints_instances)]
        created_question_retry_hints_instances = sorted(created_question_retry_hints_instances, key=lambda instance: instance.id)  # type: ignore

        # * Bulk Create Question Retry Hints Medias
        for index, one_question_retry_hint_instance in enumerate(created_question_retry_hints_instances):
            key = one_question_retry_hint_instance.text + f"_{index}"  # type: ignore
            if key in self.question_retry_hints_medias_hashmap:
                medias = [{"file": one_media["file"]} for one_media in self.question_retry_hints_medias_hashmap[key]]
                media_instances = QuestionRetryHintMediaBulkCreateSerializer(
                    data={"question_retry_hint": one_question_retry_hint_instance.id, "medias": medias}  # type: ignore
                )
                media_instances.is_valid()
                media_instances.save()

        return created_question_retry_hints_instances
