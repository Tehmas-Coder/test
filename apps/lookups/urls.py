from django.urls import include, path
from rest_framework import routers

from apps.lookups.views import (
    CountryViewset,
    CurrencyViewset,
    LanguageViewset,
    MeasuringUnitViewset,
    MediaTypeViewset,
    OrganizationViewSet,
    PackageViewset,
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
router.register(r"packages", PackageViewset)
router.register(r"organizations", OrganizationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path(
        "remove-organization-user/<int:pk>/",
        OrganizationViewSet.as_view({"delete": "remove_organization_user"}),
    ),
]


urlpatterns += router.urls
