from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.lookups.models import Media
from utils.rna_utils import color_print, debug_print
from rest_framework import serializers

MEDIA_TYPES = {
    "image": 1,
    "audio": 2,
    "video": 3,
    "document": 4,
}


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
        media_type = self.determine_media_type(file)

        media = Media.objects.create(
            name=name,
            file=file,
            extension=extension,
            size=size,
            type_id=media_type,
        )
        return media

    def determine_media_type(self, file):
        extension = file.name.split(".")[-1]
        if extension in ["jpg", "jpeg", "png", "gif"]:
            return MEDIA_TYPES["image"]
        elif extension in ["mp3", "wav", "ogg"]:
            return MEDIA_TYPES["audio"]
        elif extension in ["mp4", "avi", "mov"]:
            return MEDIA_TYPES["video"]
        else:
            return MEDIA_TYPES["document"]


class MediaBulkCreateSerializer(serializers.Serializer):
    files = serializers.ListField(child=serializers.FileField())

    def validate(self, data):
        # Initialize a list to hold individual media validation errors
        media_serializer_errors = []

        # Iterate over each file and validate it using MediaSerializer
        for file in data.get("files", []):
            media_data = {"file": file}
            media_serializer = MediaSerializer(data=media_data)

            if media_serializer.is_valid():
                # Validate successful, move to the next file
                continue
            else:
                # Collect errors
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
            media_type = self.determine_media_type(file)

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

        return media_instances

    def determine_media_type(self, file):
        extension = file.name.split(".")[-1]
        if extension in ["jpg", "jpeg", "png", "gif"]:
            return MEDIA_TYPES["image"]
        elif extension in ["mp3", "wav", "ogg"]:
            return MEDIA_TYPES["audio"]
        elif extension in ["mp4", "avi", "mov"]:
            return MEDIA_TYPES["video"]
        else:
            return MEDIA_TYPES["document"]
