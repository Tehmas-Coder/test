from rest_framework import serializers

from apps.questionbank.models import QuestionMedia
from apps.questionbank.serializers.media_serializers import (
    MediaBulkCreateSerializer,
    MediaSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionMediaEditSerializer(BaseModelSerializer):
    media = serializers.FileField(use_url=True)

    class Meta:
        model = QuestionMedia
        fields = [
            "id",
            "question",
            "media",
        ] + get_base_model_fields()

    def create(self, validated_data):
        media = validated_data.pop("media")

        # * Create media object
        media_serializer = MediaSerializer(data={"file": media})
        media_serializer.is_valid(raise_exception=True)
        media = media_serializer.save()

        # * Create question media object
        question_media = QuestionMedia.objects.create(media=media, **validated_data)

        return question_media


class QuestionMediaDetailSerializer(BaseModelSerializer):
    media = MediaSerializer()

    class Meta:
        model = QuestionMedia
        fields = [
            "id",
            "media",
        ] + get_base_model_fields()


class QuestionMediaBulkCreateSerializer(BaseModelSerializer):
    medias = serializers.ListField(child=serializers.DictField(child=serializers.FileField()), write_only=True)

    class Meta:
        model = QuestionMedia
        fields = [
            "id",
            "question",
            "medias",
        ] + get_base_model_fields()

    def create(self, validated_data):
        medias_data = validated_data.pop("medias")

        # * Bulk Create media objects
        media_serializer = MediaBulkCreateSerializer(data={"files": [media["file"] for media in medias_data]})
        media_serializer.is_valid(raise_exception=True)
        media_instances = media_serializer.save()

        # * Bulk Create question media objects
        question_media_instances = [QuestionMedia(media=media, **validated_data) for media in media_instances]
        QuestionMedia.objects.bulk_create(question_media_instances)

        created_question_media_instances = QuestionMedia.objects.all().order_by("-id")[: len(question_media_instances)]

        created_question_media_instances = sorted(created_question_media_instances, key=lambda instance: instance.id)

        return created_question_media_instances
