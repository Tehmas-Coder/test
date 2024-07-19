from rest_framework import serializers

from apps.lookups.serializers.media_serializers import MediaSerializer
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