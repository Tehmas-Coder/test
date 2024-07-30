from django.urls import include, path

urlpatterns = [
    path("", include("apps.user.urls")),
    path("", include("apps.lookups.urls")),
    path("", include("apps.questionbank.urls")),
    path("", include("apps.exam.urls")),
    path("", include("apps.student.urls")),
]
