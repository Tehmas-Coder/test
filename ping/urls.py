from django.urls import path

from ping.views import PingAPI

urlpatterns = [
    path("", PingAPI.as_view()),
]
