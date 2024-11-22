from rest_framework import serializers

from apps.lookups.models.lookup_models import Region
from apps.lookups.serializers.country_serializers import CountrySerializer


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "code",
        ]


class RegionDetailSerializer(serializers.ModelSerializer):
    countries = CountrySerializer(many=True, read_only=True)

    class Meta:
        model = Region
        fields = [
            "id",
            "name",
            "code",
            "countries",
        ]
