from django.urls import include, path
from rest_framework import routers

from apps.organization.views import OrganizationViewSet

router = routers.DefaultRouter()
router.register(r"organizations", OrganizationViewSet)

urlpatterns = [
    path("", include(router.urls)),
]

urlpatterns += router.urls
