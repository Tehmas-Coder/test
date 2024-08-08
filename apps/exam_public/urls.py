from django.urls import include, path
from rest_framework import routers

from apps.exam_public.views.exam_public_views import (
    CandidateExamViewSet,
    CandidateViewSet,
)

router = routers.DefaultRouter()

router.register(r"candidate", CandidateViewSet)
router.register(r"candidate-exam", CandidateExamViewSet)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "get-exams-backlogs-with-candidates/",
        CandidateExamViewSet.as_view({"get": "get_exam_backlogs_with_candidate_detail"}),
        name="get_exams_backlogs_with_candidates",
    ),
]


urlpatterns += router.urls
