from rest_framework import viewsets
from apps.lookups.serializers.country_serializer import CountrySerializer
from apps.lookups.models import Country


class CountryViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    permission_classes = []
    serializer_class = CountrySerializer
    queryset = Country.objects.all().prefetch_related(
        "timezones", "currencies", "languages", "states", "states__cities"
    )
