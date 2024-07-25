from rest_framework import serializers

from apps.lookups.serializers.media_serializers import MediaBulkCreateSerializer, MediaSerializer
from apps.questionbank.models import QuestionRetryHintMedia
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionRetryHintMediaSerializer(BaseModelSerializer):
    media = MediaSerializer()

    class Meta:
        model = QuestionRetryHintMedia
        fields = [
            "id",
            "question_retry_hint",
            "media",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionRetryHintMediaEditSerializer(BaseModelSerializer):
    media = serializers.FileField(use_url=True)

    class Meta:
        model = QuestionRetryHintMedia
        fields = [
            "id",
            "question_retry_hint",
            "media",
        ] + get_base_model_fields()
        read_only_fields = ["id"]

    def create(self, validated_data):
        media = validated_data.pop("media")
        media_serializer = MediaSerializer(data={"file": media})
        media_serializer.is_valid(raise_exception=True)
        media = media_serializer.save()
        question_retry_hint_media = QuestionRetryHintMedia.objects.create(media=media, **validated_data)
        question_retry_hint_media.refresh_from_db()
        return question_retry_hint_media


class QuestionRetryHintMediaDetailSerializer(BaseModelSerializer):
    media = MediaSerializer()

    class Meta:
        model = QuestionRetryHintMedia
        fields = [
            "id",
            "media",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionRetryHintMediaBulkCreateSerializer(BaseModelSerializer):
    medias = serializers.ListField(child=serializers.DictField(child=serializers.FileField()), write_only=True)

    class Meta:
        model = QuestionRetryHintMedia
        fields = [
            "id",
            "question_retry_hint",
            "medias",
        ] + get_base_model_fields()

    def create(self, validated_data):
        medias_data = validated_data.pop("medias")

        # * Bulk Create media objects
        media_serializer = MediaBulkCreateSerializer(data={"files": [media["file"] for media in medias_data]})
        media_serializer.is_valid(raise_exception=True)
        media_instances = media_serializer.save()

        # * Bulk Create question retry hint media objects
        question_retry_hint_media_instances = [QuestionRetryHintMedia(media=media, **validated_data) for media in media_instances]
        QuestionRetryHintMedia.objects.bulk_create(question_retry_hint_media_instances)

        created_question_retry_hint_media_instances = QuestionRetryHintMedia.objects.all().order_by("-id")[: len(question_retry_hint_media_instances)]

        return created_question_retry_hint_media_instances
