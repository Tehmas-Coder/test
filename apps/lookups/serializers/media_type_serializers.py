from rest_framework import serializers
from apps.lookups.models import MediaType


class MediaTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MediaType
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "description",
        ]
