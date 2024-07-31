from django.shortcuts import render
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.candiate_serializers import (
    CandidateDetailSerializer,
    CandidateSerializer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamSerializer,
)

# ---------------------------------------------------------------------------- #
#                                   CANDIDATE                                  #
# ---------------------------------------------------------------------------- #


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.objects.all().select_related("user", "user__country")
    serializer_class = CandidateSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return CandidateDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        serializer = CandidateDetailSerializer(response)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------------ CANDIDATE EXAM ------------------------------ #


class CandidateExamViewSet(viewsets.ModelViewSet):
    queryset = CandidateExam.objects.all().select_related("candidate", "exam", "schedule")
    serializer_class = CandidateExamSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch"]
