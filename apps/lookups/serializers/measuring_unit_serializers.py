from rest_framework import serializers
from apps.lookups.models import MeasuringUnit


class MeasuringUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasuringUnit
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "description",
        ]
