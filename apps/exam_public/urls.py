from django.urls import include, path
from rest_framework import routers

from apps.exam_public.views.exam_public_views import (
    CandidateExamViewSet,
    CandidateViewSet,
    ExamBacklogViewSet,
)

router = routers.DefaultRouter()

router.register(r"candidate", CandidateViewSet)
router.register(r"candidate-exam", CandidateExamViewSet)
router.register(r"exam-backlog", ExamBacklogViewSet)


urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
