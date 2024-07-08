from rest_framework import serializers
from apps.lookups.models import Country
from apps.lookups.serializers.timezone_serializers import TimezoneSerializer
from apps.lookups.serializers.currency_serializers import CurrencySerializer
from apps.lookups.serializers.language_serializers import LanguageSerializer
from apps.lookups.serializers.state_serializers import StateSerializer


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            "id",
            "name",
            "iso2_code",
            "iso3_code",
            "capital",
            "lat",
            "lon",
            "dial_code",
            "is_un_member",
            "flag",
        ]


class CountryDetailSerializer(serializers.ModelSerializer):
    timezones = TimezoneSerializer(many=True, read_only=True)
    currencies = CurrencySerializer(many=True, read_only=True)
    languages = LanguageSerializer(many=True, read_only=True)
    states = StateSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = [
            "id",
            "name",
            "iso2_code",
            "iso3_code",
            "capital",
            "lat",
            "lon",
            "dial_code",
            "is_un_member",
            "flag",
            "timezones",
            "currencies",
            "languages",
            "states",
        ]
