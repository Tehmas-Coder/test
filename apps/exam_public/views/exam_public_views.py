from django.db.models import Prefetch
from django.forms import model_to_dict
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializerForBacklogs
from apps.exam_public.classes.exam_backlogs_helper import ExamBacklogs
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklog,
    ExamBacklogQuestion,
    ExamBacklogQuestionCountry,
    SectionBacklog,
)
from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogEditSerializer,
)
from apps.exam_public.serializers.candiate_serializers import (
    CandidateDetailSerializer,
    CandidateSerializer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamDetailSerializer,
    CandidateExamEditSerializer,
    CandidateExamListSerializer,
)
from apps.user.models import BaseUser
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

    def get_queryset(self):
        if self.action == "retrieve":
            return self.queryset.prefetch_related(
                Prefetch(
                    "exam_backlog__backlog_questions",
                    queryset=ExamBacklogQuestion.objects.filter()
                    .prefetch_related(
                        "backlog_tags",
                        "backlog_choices",
                        "backlog_choices__exambacklogquestionchoicemedia_set",
                        "backlog_choices__exambacklogquestionchoicemedia_set__media",
                        "backlog_attempt_responses",
                        "backlog_retry_hints",
                        "backlog_retry_hints__exambacklogquestionretryhintmedia_set",
                        "backlog_retry_hints__exambacklogquestionretryhintmedia_set__media",
                        "exambacklogquestionmedia_set",
                        "exambacklogquestionmedia_set__media",
                        "exambacklogquestioncountry_set",
                    )
                    .select_related(
                        "type",
                        "measuring_unit",
                        "difficulty_level",
                        "section_backlog",
                        "section_backlog__measuring_unit",
                        "subsection_backlog",
                        "subsection_backlog__measuring_unit",
                    ),
                ),
                Prefetch(
                    "exam_backlog__section_backlogs",
                    SectionBacklog.objects.all().prefetch_related("subsection_backlogs"),
                ),
            )
        return super().get_queryset()

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
        exam_data = ExamDetailSerializerForBacklogs(exam_instance).data
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

    # def retrieve(self, request, *args, **kwargs):
    #     candidate_exam_data = model_to_dict(CandidateExam.objects.get(id=self.kwargs["pk"]))
    #     candidate_id = candidate_exam_data["candidate"]
    #     exam_backlog_id = candidate_exam_data["exam_backlog"]
    #     exam_question_backlog = list(ExamBacklogQuestion.objects.filter(exam_backlog_id=exam_backlog_id).values("is_global", "id"))

    #     is_global_exam_question_backlog_ids_list = []
    #     is_not_global_exam_question_backlog_ids_list = []
    #     for one_question in exam_question_backlog:
    #         one_question_backlog_id = one_question["id"]

    #         if one_question["is_global"]:
    #             is_global_exam_question_backlog_ids_list.append(one_question_backlog_id)
    #         else:
    #             user_country_id = BaseUser.objects.get(pk=candidate_id).country_id
    #             exam_question_backlog_ids_for_user_country = ExamBacklogQuestionCountry.objects.get(
    #                 exam_backlog_question_id=one_question_backlog_id, country_id=user_country_id
    #             ).exam_backlog_question_id

    #             is_not_global_exam_question_backlog_ids_list.append(exam_question_backlog_ids_for_user_country)
    #     final_user_backlog_question_ids_list = is_global_exam_question_backlog_ids_list + is_not_global_exam_question_backlog_ids_list

    #     final_user_backlog_question_list = CandidateExam.objects.filter().prefetch_related(
    #         Prefetch(
    #             "exam_backlog__backlog_questions",
    #             queryset=ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list)
    #             .prefetch_related(
    #                 "type",
    #                 "backlog_tags",
    #                 "backlog_choices",
    #                 "backlog_choices__exambacklogquestionchoicemedia_set",
    #                 "backlog_choices__exambacklogquestionchoicemedia_set__media",
    #                 "backlog_attempt_responses",
    #                 "backlog_retry_hints",
    #                 "backlog_retry_hints__exambacklogquestionretryhintmedia_set",
    #                 "backlog_retry_hints__exambacklogquestionretryhintmedia_set__media",
    #                 "exambacklogquestionmedia_set",
    #                 "exambacklogquestionmedia_set__media",
    #                 "exambacklogquestioncountry_set",
    #             )
    #             .select_related(
    #                 "section_backlog",
    #                 "subsection_backlog",
    #             ),
    #         ),
    #         Prefetch(
    #             "exam_backlog__section_backlogs",
    #             SectionBacklog.objects.all().prefetch_related("subsection_backlogs"),
    #         ),
    #     )

    #     return Response(final_user_backlog_question_list, status=status.HTTP_200_OK)
