from rest_framework import serializers
from apps.lookups.models import Currency


class CurrencySerializer(serializers.ModelSerializer):
    class Meta:
        model = Currency
        fields = [
            "id",
            "name",
            "code",
        ]
