from django.urls import path
from rest_framework import routers
from django.urls import include
from apps.lookups.views import (
    CountryViewset,
    CurrencyViewset,
    LanguageViewset,
    MeasuringUnitViewset,
    MediaTypeViewset,
    RegionViewset,
    StateViewset,
    TagViewset,
    TimezoneViewset,
)


router = routers.DefaultRouter()


router.register(r"countries", CountryViewset)
router.register(r"timezones", TimezoneViewset)
router.register(r"regions", RegionViewset)
router.register(r"states", StateViewset)
router.register(r"languages", LanguageViewset)
router.register(r"currencies", CurrencyViewset)
router.register(r"measuring-units", MeasuringUnitViewset)
router.register(r"media-types", MediaTypeViewset)
router.register(r"tags", TagViewset)

urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
