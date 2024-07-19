from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionChoice
from apps.questionbank.serializers.media_serializers import MediaSerializer
from utils.rna_utils import debug_print


class QuestionChoiceSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True)

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

    def validate_empty_values(self, data):
        debug_print(data, "cyan")
        return super().validate_empty_values(data)

    def validate(self, attrs):
        debug_print(attrs, "cyan")
        return super().validate(attrs)

    def create(self, validated_data):
        debug_print(validated_data)
        medias = validated_data.pop("medias", [])
        question_choice = QuestionChoice.objects.create(**validated_data)

        for media in medias:
            media_serializer = MediaSerializer(data=media)
            media_serializer.is_valid(raise_exception=True)
            media = media_serializer.save()
            question_choice.medias.add(media)

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
