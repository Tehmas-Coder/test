from django.db.models import Prefetch, Q
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam, ExamSubjectQuestion, Section
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializer
from apps.exam_public.classes.candidate_exam_backlogs_helper import (
    CandidateExamBacklogs,
)
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
            "exam",
            "schedule",
            "candidate",
            "candidate__user",
            "candidate__user__country",
            "exam__education_level",
        )
        .prefetch_related(
            "candidate__user__roles",
            "exam__examsubject_set",
            "exam__examsubject_set__subject",
            Prefetch(
                "exam__examsubject_set__examsubjectquestion_set",
                queryset=ExamSubjectQuestion.objects.filter(
                    Q(
                        Q(section__isnull=True)
                        | Q(subsection__isnull=True)
                        | Q(
                            section__isnull=False,
                            section__meta_status="active",
                        )
                        | Q(
                            subsection__isnull=False,
                            subsection__meta_status="active",
                        )
                    )
                ).select_related("section", "subsection"),
            ),
            Prefetch(
                "exam__sections",
                queryset=Section.objects.filter(meta_status="active").prefetch_related("subsections"),
            ),
            Prefetch(
                "exam__examsubject_set__examsubjectquestion_set__question",
                queryset=Question.get_detail_queryset(),
            ),
        )
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        candidate_exam_instances = serializer.save()
        # * Fetching newly created instances
        created_candidate_exam_instances = self.get_queryset().order_by("-created_at")[: len(candidate_exam_instances)]
        created_candidate_exam_instances = sorted(created_candidate_exam_instances, key=lambda instance: instance.id)  # type:ignore

        # * Creating Backlogs for Candidate Exam
        candidate_exam_data = CandidateExamDetailSerializer(created_candidate_exam_instances, many=True).data
        candidate_exam_backlogs = CandidateExamBacklogs(candidate_exam_list=candidate_exam_data)  # type: ignore
        candidate_exam_backlogs.create_backlogs()

        response_data = CandidateExamListSerializer(created_candidate_exam_instances, many=True).data
        return Response(response_data, status=status.HTTP_201_CREATED)
