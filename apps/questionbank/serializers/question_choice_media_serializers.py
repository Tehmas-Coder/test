from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionChoiceMedia
from apps.lookups.serializers.media_serializers import MediaSerializer
from utils.rna_utils import debug_print
from rest_framework import serializers

class QuestionChoiceMediaSerializer(BaseModelSerializer):
    media = MediaSerializer()
    class Meta:
        model = QuestionChoiceMedia
        fields = [
            "id",
            "question_choice",
            "media"
        ] + get_base_model_fields()

        read_only_fields = ["id"]


class QuestionChoiceMediaEditSerializer(BaseModelSerializer):
    media = serializers.FileField(use_url=True)
    class Meta:
        model = QuestionChoiceMedia
        fields = [
            "id",
            "question_choice",
            "media"
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
