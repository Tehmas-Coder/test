from rest_framework import serializers
from apps.lookups.models import Language


class LanguageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Language
        fields = [
            "id",
            "name",
            "code",
        ]
