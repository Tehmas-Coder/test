from django.urls import path, include


urlpatterns = [
    path("", include("apps.user.urls")),
    path("", include("apps.lookups.urls")),
    path("", include("apps.questionbank.urls")),
]
