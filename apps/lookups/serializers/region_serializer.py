from rest_framework import serializers
from apps.lookups.models import Region


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "code",
        ]
