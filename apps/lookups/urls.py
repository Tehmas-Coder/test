from django.urls import path
from rest_framework import routers
from django.urls import include
from apps.lookups.views import CountryViewset


router = routers.DefaultRouter()


router.register(r"countries", CountryViewset)

urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
