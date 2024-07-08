from rest_framework import serializers
from apps.lookups.models import Tag


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "description",
        ]
