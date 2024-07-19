from django.urls import path
from rest_framework import routers
from django.urls import include
from apps.questionbank.views.question_views import (
    EducationLevelViewSet,
    QuestionChoiceViewSet,
    QuestionMediaViewSet,
    QuestionTagViewSet,
    QuestionViewSet,
    SubjectEducationLevelViewSet,
    SubjectViewSet,
)


router = routers.DefaultRouter()


router.register(r"subjects", SubjectViewSet)
router.register(r"education-levels", EducationLevelViewSet)
router.register(r"subject-education-levels", SubjectEducationLevelViewSet)
router.register(r"questions", QuestionViewSet)
router.register(r"question-media", QuestionMediaViewSet)
router.register(r"question-tag", QuestionTagViewSet)
router.register(r"question-choice", QuestionChoiceViewSet)

urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
