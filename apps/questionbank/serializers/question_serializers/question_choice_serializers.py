from apps.questionbank.serializers.question_serializers.question_choice_media_serializers import (
    QuestionChoiceMediaDetailSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionChoice
from apps.lookups.serializers.media_serializers import MediaSerializer
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

    def create(self, validated_data):
        try:
            request = self.context.get("request")
            medias = []
            for file in request.FILES:  # type: ignore
                medias.append({"file": request.FILES[file]})  # type: ignore
        except:
            medias = validated_data.pop("medias")

        question_choice = QuestionChoice.objects.create(**validated_data)

        for media in medias:
            media_serializer = MediaSerializer(data=media)
            media_serializer.is_valid(raise_exception=True)
            media = media_serializer.save()
            question_choice.medias.add(media)

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
    medias = QuestionChoiceMediaDetailSerializer(
        many=True, required=False, source="questionchoicemedia_set"
    )

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
