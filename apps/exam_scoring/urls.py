from django.urls import path
from rest_framework import routers

from apps.exam_scoring.views.exam_scoring_views import (
    CandidateExamScoringViewset,
    ExamReportAPIView,
)

router = routers.DefaultRouter()


urlpatterns = [
    path("mark-candidate-exam/", CandidateExamScoringViewset.as_view({"post": "candidate_exam_marking"})),
    path("candidate-exam-scoresheet/<str:id>/", CandidateExamScoringViewset.as_view({"get": "candidate_exam_scoresheet"})),
    path("exam-report/", ExamReportAPIView.as_view()),
]

urlpatterns += router.urls
