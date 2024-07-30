from django.urls import include, path
from rest_framework import routers

from apps.exam_public.views.views import CandidateViewSet

router = routers.DefaultRouter()

router.register(r"candidate", CandidateViewSet)


urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
