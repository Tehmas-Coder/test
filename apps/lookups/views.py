from rest_framework import viewsets

from apps.lookups.models import (
    Country,
    Currency,
    Language,
    MeasuringUnit,
    MediaType,
    Package,
    Region,
    State,
    Tag,
    Timezone,
)
from apps.lookups.serializers.country_serializers import (
    CountryDetailSerializer,
    CountrySerializer,
)
from apps.lookups.serializers.currency_serializers import CurrencySerializer
from apps.lookups.serializers.language_serializers import LanguageSerializer
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.lookups.serializers.media_type_serializers import MediaTypeSerializer
from apps.lookups.serializers.package_serializers import PackageSerializer
from apps.lookups.serializers.region_serializers import RegionDetailSerializer
from apps.lookups.serializers.state_serializers import StateSerializer
from apps.lookups.serializers.tag_serializers import TagSerializer
from apps.lookups.serializers.timezone_serializers import TimezoneSerializer


class TimezoneViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    pagination_class = None
    serializer_class = TimezoneSerializer
    queryset = Timezone.objects.all()
    pagination_class = None


class RegionViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = RegionDetailSerializer
    queryset = Region.objects.all().prefetch_related("countries")
    pagination_class = None


class CountryViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = CountryDetailSerializer
    queryset = Country.objects.all().prefetch_related("timezones", "currencies", "languages", "states", "states__cities")
    pagination_class = None

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            return CountrySerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


class StateViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = StateSerializer
    queryset = State.objects.all()
    pagination_class = None


class LanguageViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = LanguageSerializer
    queryset = Language.objects.all()
    pagination_class = None


class CurrencyViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    pagination_class = None
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    pagination_class = None


class MeasuringUnitViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = MeasuringUnitSerializer
    pagination_class = None
    queryset = MeasuringUnit.objects.all()


class MediaTypeViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = MediaTypeSerializer
    pagination_class = None
    queryset = MediaType.objects.all()


class TagViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()


class PackageViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = PackageSerializer
    pagination_class = None
    queryset = Package.objects.all()
