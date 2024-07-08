from rest_framework import serializers
from apps.lookups.models import Timezone


class TimezoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = Timezone
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
        ]
