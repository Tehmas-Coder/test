from django.urls import path

from .views import ping_views

urlpatterns = [path("/ping/", ping_views.PingAPI.as_view())]
