from rest_framework import serializers

from apps.lookups.models.lookup_models import City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["id", "name", "code", "is_capital"]
