from rest_framework import serializers

from apps.questionbank.models.question_models import QuestionChoiceMedia
from apps.questionbank.serializers.media_serializers import (
    MediaBulkCreateSerializer,
    MediaSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionChoiceMediaSerializer(BaseModelSerializer):
    media = serializers.FileField(use_url=True)

    class Meta:
        model = QuestionChoiceMedia
        fields = [
            "id",
            "question_choice",
            "media",
        ] + get_base_model_fields()

        read_only_fields = ["id"]

    def create(self, validated_data):
        media = validated_data.pop("media")
        media_serializer = MediaSerializer(data={"file": media})
        media_serializer.is_valid(raise_exception=True)
        media = media_serializer.save()
        question_choice_media = QuestionChoiceMedia.objects.create(media=media, **validated_data)
        question_choice_media.refresh_from_db()
        return question_choice_media

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["media"] = MediaSerializer(instance.media).data
        if self.context.get("rem_question_choice", False):
            del rep["question_choice"]
        return rep


class QuestionChoiceMediaBulkCreateSerializer(BaseModelSerializer):
    medias = serializers.ListField(child=serializers.DictField(child=serializers.FileField()), write_only=True)

    class Meta:
        model = QuestionChoiceMedia
        fields = [
            "id",
            "question_choice",
            "medias",
        ] + get_base_model_fields()

    def create(self, validated_data):
        medias_data = validated_data.pop("medias")

        # * Bulk Create media objects
        media_serializer = MediaBulkCreateSerializer(data={"files": [media["file"] for media in medias_data]})
        media_serializer.is_valid(raise_exception=True)
        media_instances = media_serializer.save()

        # * Bulk Create question choice media objects
        question_choice_media_instances = [QuestionChoiceMedia(media=media, **validated_data) for media in media_instances]
        QuestionChoiceMedia.objects.bulk_create(question_choice_media_instances)
        created_question_choice_media_instances = (
            QuestionChoiceMedia.objects.all().select_related("media").order_by("-id")[: len(question_choice_media_instances)]
        )
        return sorted(created_question_choice_media_instances, key=lambda instance: instance.pk)
