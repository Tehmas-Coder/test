from django.db.models import Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam, ExamSubjectQuestion, Section
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializer
from apps.exam_public.classes.exam_backlogs_helper import ExamBacklogs
from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.candiate_serializers import (
    CandidateDetailSerializer,
    CandidateSerializer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamDetailSerializer,
    CandidateExamEditSerializer,
    CandidateExamListSerializer,
)
from apps.questionbank.models import Question
from utils.rna_utils import debug_print

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
    queryset = (
        CandidateExam.objects.all()
        .select_related(
            "exam_backlog",
            "schedule",
            "candidate",
            "candidate__user",
            "candidate__user__country",
        )
        .prefetch_related("candidate__user__roles")
    )
    serializer_class = CandidateExamEditSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateExamListSerializer
        if self.action == "retrieve":
            return CandidateExamDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        request_data = request.data
        exam_id = request_data.pop("exam")
        exam_instance = Exam.get_detail_queryset().get(pk=exam_id)

        # * Creating Backlogs for Exam
        exam_data = ExamDetailSerializer(exam_instance).data
        exam_backlogs = ExamBacklogs(exam_data=exam_data)
        exambacklog_id = exam_backlogs.create_backlogs()

        # * Assigning Exam to Candidates
        request_data["exam_backlog"] = exambacklog_id
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        candidate_exam_instances = serializer.save()
        # * Fetching newly created instances
        created_candidate_exam_instances = self.get_queryset().order_by("-created_at")[: len(candidate_exam_instances)]
        created_candidate_exam_instances = sorted(created_candidate_exam_instances, key=lambda instance: instance.id)

        response_data = CandidateExamListSerializer(created_candidate_exam_instances, many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)
