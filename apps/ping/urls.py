from django.urls import path

from .views.ping_views import PingAPI

urlpatterns = [
    path("ping/", PingAPI.as_view()),
]
