from django.urls import path

from .views import ping_views

urlpatterns = [path("/pings/", ping_views.PingAPI.as_view())]
