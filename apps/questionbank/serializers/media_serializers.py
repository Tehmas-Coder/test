from rest_framework import serializers

from apps.user.models.user_models import Media
from core.serializers import BaseModelSerializer, get_base_model_fields

MEDIA_TYPES = {
    "image": 1,
    "audio": 2,
    "video": 3,
    "document": 4,
}


def determine_media_type(file):
    extension = file.name.split(".")[-1]
    if extension in ["jpg", "jpeg", "png", "gif"]:
        return MEDIA_TYPES["image"]
    elif extension in ["mp3", "wav", "ogg"]:
        return MEDIA_TYPES["audio"]
    elif extension in ["mp4", "avi", "mov"]:
        return MEDIA_TYPES["video"]
    else:
        return MEDIA_TYPES["document"]


class MediaSerializer(BaseModelSerializer):
    file = serializers.FileField(use_url=True)

    class Meta:
        model = Media
        fields = [
            "id",
            "name",
            "file",
            "type",
            "extension",
            "size",
        ] + get_base_model_fields()

        read_only_fields = ["id", "size", "name", "type", "extension"]

    def create(self, validated_data):
        file = validated_data.pop("file")
        name = file.name
        extension = file.name.split(".")[-1]
        size = file.size
        media_type = determine_media_type(file)

        media = Media.objects.create(
            name=name,
            file=file,
            extension=extension,
            size=size,
            type_id=media_type,
        )
        return media


class MediaBulkCreateSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField())

    def validate(self, data):
        media_serializer_errors = []
        for file in data.get("files", []):
            media_data = {"file": file}
            media_serializer = MediaSerializer(data=media_data)
            if not media_serializer.is_valid():
                media_serializer_errors.append(media_serializer.errors)
        if media_serializer_errors:
            raise serializers.ValidationError({"file_errors": media_serializer_errors})
        return data

    def create(self, validated_data):
        files = validated_data.get("files", [])
        media_instances = []
        for file in files:
            name = file.name
            extension = file.name.split(".")[-1]
            size = file.size
            media_type = determine_media_type(file)

            media_instance = Media(
                name=name,
                file=file,
                extension=extension,
                size=size,
                type_id=media_type,
            )
            media_instances.append(media_instance)

        # Bulk create media instances
        Media.objects.bulk_create(media_instances)
        created_media_instances = Media.objects.all().order_by("-created_at")[: len(media_instances)]
        created_media_instances = sorted(created_media_instances, key=lambda instance: instance.id)  # type:ignore
        return created_media_instances
