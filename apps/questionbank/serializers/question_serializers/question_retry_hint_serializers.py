from apps.lookups.serializers.media_serializers import MediaSerializer
from apps.questionbank.models import QuestionRetryHint
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class QuestionRetryHintSerializer(BaseModelSerializer):
    medias = MediaSerializer(many=True, required=False)

    class Meta:
        model = QuestionRetryHint
        fields = [
            "id",
            "question",
            "text",
            "has_media",
            "sequence",
            "medias",
        ] + get_base_model_fields()
        read_only_fields = ["id"]

    def create(self, validated_data):
        try:
            request = self.context.get("request")
            medias = []
            for file in request.FILES: #type: ignore
                medias.append({"file": request.FILES[file]}) #type: ignore
        except:
            medias = validated_data.pop("medias")

        retry_hint = QuestionRetryHint.objects.create(**validated_data)
        for media in medias:
            media_serializer = MediaSerializer(data=media)
            media_serializer.is_valid(raise_exception=True)
            media = media_serializer.save()
            retry_hint.medias.add(media)
        retry_hint.refresh_from_db()
        return retry_hint


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
