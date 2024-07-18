from apps.questionbank.models import QuestionRetryHint
from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.serializers.media_serializers import MediaSerializer


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
