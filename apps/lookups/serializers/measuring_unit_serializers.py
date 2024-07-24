from rest_framework import serializers
from apps.lookups.models import MeasuringUnit
from core.serializers import BaseModelSerializer


class MeasuringUnitSerializer(BaseModelSerializer):
    class Meta:
        model = MeasuringUnit
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "description",
        ] + BaseModelSerializer.Meta.fields
