from django.urls import include, path
from rest_framework import routers

from apps.exam_public.views.exam_public_views import (
    CandidateExamAnswerViewset,
    CandidateExamViewSet,
    CandidateViewSet,
)

router = routers.DefaultRouter()

router.register(r"candidate", CandidateViewSet)
router.register(r"candidate-exam", CandidateExamViewSet)
router.register(r"candidate-exam-answer", CandidateExamAnswerViewset)


urlpatterns = [
    path("", include(router.urls)),
]


urlpatterns += router.urls
