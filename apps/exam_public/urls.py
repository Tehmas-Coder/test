from django.urls import include, path
from rest_framework import routers

from apps.exam_public.views.exam_public_views import (
    CandidateExamAnswerViewset,
    CandidateExamViewSet,
    CandidateViewSet,
    ExamBacklogAnswerKeyAPI,
)

router = routers.DefaultRouter()

router.register(r"candidate", CandidateViewSet)
router.register(r"candidate-exam", CandidateExamViewSet)
router.register(r"candidate-exam-answer", CandidateExamAnswerViewset)


urlpatterns = [
    path("", include(router.urls)),
    path(
        "get-exams-backlogs-with-candidates/",
        CandidateExamViewSet.as_view({"get": "get_exam_backlogs_with_candidate_detail"}),
        name="get_exams_backlogs_with_candidates",
    ),
    path("exam-backlog-answers-key/<int:pk>/", ExamBacklogAnswerKeyAPI.as_view(), name="exam_backlog_answers_key"),
    path("get-exams-backlogs-with-candidates/", CandidateExamViewSet.as_view({"get": "get_exam_backlogs_with_candidate_detail"})),
    path("send-exam-link-to-users/", CandidateExamViewSet.as_view({"post": "send_exam_link_to_users"})),
]


urlpatterns += router.urls
