from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionChoice
from apps.questionbank.serializers.media_serializers import MediaSerializer


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
