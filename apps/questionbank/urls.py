from django.urls import path
from rest_framework import routers
from django.urls import include
from apps.questionbank.views.question_views import (
    EducationLevelViewSet,
    QuestionViewSet,
    SubjectEducationLevelViewSet,
    SubjectViewSet,
)


router = routers.DefaultRouter()


router.register(r"subjects", SubjectViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"subject-education-levels", SubjectEducationLevelViewSet)
router.register(r"education-levels", EducationLevelViewSet)

urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
