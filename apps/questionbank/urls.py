from django.urls import include, path
from rest_framework import routers

from apps.questionbank.views.question_views import (
    EducationLevelViewSet,
    QuestionAttemptResponseViewSet,
    QuestionChoiceMediaViewSet,
    QuestionChoiceViewSet,
    QuestionMediaViewSet,
    QuestionRetryHintMediaViewSet,
    QuestionRetryHintViewSet,
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
router.register(r"question-choice-media", QuestionChoiceMediaViewSet)
router.register(r"question-attempt-response", QuestionAttemptResponseViewSet)
router.register(r"question-retry-hint", QuestionRetryHintViewSet)
router.register(r"question-retry-hint-media", QuestionRetryHintMediaViewSet)

urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
