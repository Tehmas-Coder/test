from rest_framework import serializers

from apps.lookups.models.lookup_models import State
from apps.lookups.serializers.city_serializer import CitySerializer


class StateSerializer(serializers.ModelSerializer):
    cities = CitySerializer(many=True, read_only=True)

    class Meta:
        model = State
        fields = ["id", "name", "code", "cities"]
