from apps.lookups.models import Country
from apps.lookups.serializers.currency_serializers import CurrencySerializer
from apps.lookups.serializers.language_serializers import LanguageSerializer
from apps.lookups.serializers.state_serializers import StateSerializer
from apps.lookups.serializers.timezone_serializers import TimezoneSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CountrySerializer(BaseModelSerializer):
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
        ] + get_base_model_fields()


class CountryDetailSerializer(BaseModelSerializer):
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
        ] + get_base_model_fields()
