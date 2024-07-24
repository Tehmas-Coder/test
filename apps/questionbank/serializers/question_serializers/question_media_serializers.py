from rest_framework import serializers

from apps.lookups.serializers.media_serializers import MediaSerializer
from apps.questionbank.models import QuestionMedia
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


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
    medias = serializers.ListField(child=serializers.FileField(use_url=True), write_only=True)

    class Meta:
        model = QuestionMedia
        fields = [
            "id",
            "question",
            "medias",
        ] + get_base_model_fields()

    def create(self, validated_data):
        medias = validated_data.pop("medias")

        # * Create bulk media objects
        media_serializer = MediaSerializer(data={"file": media})
        media_serializer.is_valid(raise_exception=True)
        media = media_serializer.save()

        # * Create question media object
        question_media = QuestionMedia.objects.create(media=media, **validated_data)

        return question_media
