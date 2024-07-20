from django.urls import include, path
from rest_framework import routers

from apps.exam.views.exam_views import (
    ExamSubjectQuestionViewSet,
    ExamSubjectViewSet,
    ExamViewSet,
)

router = routers.DefaultRouter()

router.register(r"exams", ExamViewSet)
router.register(r"exam-subject", ExamSubjectViewSet)
router.register(r"exam-subject-question", ExamSubjectQuestionViewSet)


urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
