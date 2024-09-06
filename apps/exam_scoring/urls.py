from django.urls import path
from rest_framework import routers

from apps.exam_scoring.views.exam_scoring_views import CandidateExamScoringViewset

router = routers.DefaultRouter()


urlpatterns = [
    path("mark-candidate-exam/", CandidateExamScoringViewset.as_view({"post": "candidate_exam_marking"})),
    path("score-candidate-exam/", CandidateExamScoringViewset.as_view({"post": "candidate_exam_scoring"})),
]

urlpatterns += router.urls
