import datetime
import json

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializerForBacklogs
from apps.exam_admin.utils.exam_utils import RandomExamCreator
from apps.exam_public.custom.candidate_exam_classes import CandidateExamNinja
from apps.exam_public.custom.exam_backlogs_classes import ExamBacklogsNinja
from apps.exam_public.filters.candidate_exam_filters import CandidateExamFilterBackend
from apps.exam_public.filters.candidate_filters import CandidateFilterBackend
from apps.exam_public.filters.exam_backlog_filters import get_exambacklog_q_filter
from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklog,
    ExamBacklogQuestion,
    ExamBacklogQuestionChoice,
)
from apps.exam_public.models.exam_public_models import (
    Candidate,
    CandidateExam,
    CandidateExamAnswer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_serializer import (
    ExamBacklogQuestionChoiceForKeySerializer,
)
from apps.exam_public.serializers.candidate_exam_answer_serializers import (
    CandidateExamAnswerSerializer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamDetailSerializer,
    CandidateExamEditSerializer,
    CandidateExamListSerializer,
    CandidateExamWithAnswersDetailSerializer,
    ExamBacklogWithCandidateDetailsSerializer,
)
from apps.exam_public.serializers.candidate_serializers import CandidateSerializer
from apps.user.utils.user_utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from utils.datetime_utils import convert_any_datetime_to_utc
from utils.rna_utils import debug_print, make_error_response

# ---------------------------------------------------------------------------- #
#                                   CANDIDATE                                  #
# ---------------------------------------------------------------------------- #


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = Candidate.get_detail_queryset(organization=True, user=True)
    serializer_class = CandidateSerializer
    filter_backends = [CandidateFilterBackend]
    pagination_class = None
    http_method_names = ["get", "post", "patch"]

    def get_serializer_context(self):
        if self.action in ["list", "retrieve"]:
            return {"selector": True}
        return super().get_serializer_context()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        if Candidate.objects.filter(user_id=request.data["user"], organization_id=request.data.get("organization")).exists():
            return make_error_response(data=request.data, message="Candidate with this organization already exists.")
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        response = serializer.save()
        serializer = CandidateSerializer(response, context={"selector": True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------- #
#                                CANDIDATE EXAM                                #
# ---------------------------------------------------------------------------- #


class CandidateExamViewSet(viewsets.ModelViewSet):
    queryset = CandidateExam.get_detail_queryset(exam_backlog=True, candidate=True, is_organization_filter=True)
    serializer_class = CandidateExamEditSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [CandidateExamFilterBackend]

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateExamListSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = request.data
        organization = None if get_current_user().is_superuser else get_current_user_organization()  # type:ignore
        request_data["organization_id"] = organization
        exam_id = request_data.get("exam")
        if exam_id:
            request_data.pop("exam")
            exam_instance = Exam.get_detail_queryset(all=True, q_filter=Q(id=exam_id)).first()
            # * Creating Backlogs for Exam
            exam_data = ExamDetailSerializerForBacklogs(exam_instance).data
            exam_backlogs = ExamBacklogsNinja(exam_data=exam_data)  # type:ignore
            request_data["exam_backlog"] = exam_backlogs.create_backlogs()

        # * Assigning Exam to Candidates
        if request_data.get("start_datetime") and request_data.get("end_datetime"):
            if isinstance(request_data["start_datetime"], datetime.datetime):
                request_data["start_datetime"] = convert_any_datetime_to_utc(request_data["start_datetime"])
            if isinstance(request_data["end_datetime"], datetime.datetime):
                request_data["end_datetime"] = convert_any_datetime_to_utc(request_data["end_datetime"])
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        candidate_exam_instances = serializer.save()

        # * Fetching newly created instances
        created_candidate_exam_instances = self.get_queryset().order_by("-created_at")[: len(candidate_exam_instances)]
        created_candidate_exam_instances = sorted(created_candidate_exam_instances, key=lambda instance: instance.id)
        response_data = CandidateExamListSerializer(created_candidate_exam_instances, many=True).data
        candidate_exam_ids = [one_candidate_exam["id"] for one_candidate_exam in response_data]

        # * Sending Exam Invitation Emails
        if request_data.get("is_send_invitation_emails"):
            CandidateExamNinja().send_exam_invitation_link(candidate_exam_ids)

        # * Appending Token to Candidate Exam Data if request is from Student Apply
        if request_data.get("append_tokens"):
            candidate_exam_id_token_hashmap = CandidateExamNinja().get_candidate_exam_tokens(candidate_exam_ids)
            for one_candidate_exam in response_data:
                one_candidate_exam["token"] = candidate_exam_id_token_hashmap.get(one_candidate_exam["id"])

        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        candidate_exam_backlog_question_instance = CandidateExamNinja().get_candidate_exam(candidate_exam_id)
        data = CandidateExamDetailSerializer(
            candidate_exam_backlog_question_instance, context={"get_retry_hints": candidate_exam_backlog_question_instance.is_preparatory}  # type: ignore
        ).data
        return Response(data, status=status.HTTP_200_OK)

    @transaction.atomic
    @action(detail=False, methods=["post"], url_path="candidate-self-preparatory-exam")
    def candidate_self_preparatory_exam(self, request):
        current_user = get_current_user()
        request_data = request.data
        organization_id = request_data.get("organization")
        try:
            candidate = Candidate.objects.get(
                user_id=current_user.id, organization_id=organization_id, is_self_preparation_allowed=True  # type:ignore
            )
        except Exception:
            return make_error_response(message="You are not allowed to create self preparatory exams with requested organization.")
        if not candidate.is_exam_limit_remaining:
            return make_error_response(message="You have reached the limit of creating self preparatory exams with this organization.")
        is_exam_preparatory = request_data.get("is_preparatory", "False")
        exam_duration = request_data.get("exam_duration")
        exam_questions_visibility = request_data.get("exam_questions_visibility")
        request_data["question_types"] = [1, 2]

        # * Random Exam Creation
        create_random_exam_instance = RandomExamCreator(
            exam_data=request_data.get("exam_data"),
            subject_education_levels=request_data.get("subjects"),
            difficulty_levels=request_data.get("difficulty_levels"),
            question_types=request_data.get("question_types"),
            question_count=request_data.get("question_count"),
            is_candidate=True,
            organization_id=organization_id,
        )
        exam_instance = create_random_exam_instance.create_random_exam()
        candidate.self_exam_count += 1
        candidate.save()
        exam_instance = Exam.get_detail_queryset(all=True, q_filter=Q(pk=exam_instance.pk)).first()

        # * Exam Backlog Creation
        exam_data = ExamDetailSerializerForBacklogs(exam_instance).data
        exam_backlogs = ExamBacklogsNinja(exam_data=exam_data)  # type:ignore
        exam_backlog_id = exam_backlogs.create_backlogs()

        # * Candidate Exam Creation
        candidate_exam_data = {
            "candidate_id": candidate.id,  # type:ignore
            "candidate_email": current_user.email,  # type:ignore
            "exam_backlog_id": exam_backlog_id,
            "is_preparatory": is_exam_preparatory,
            "exam_duration": exam_duration,
            "exam_questions_visibility": exam_questions_visibility,
            "is_created_by_candidate": True,
        }
        candidate_exam_instance = CandidateExam.objects.create(**candidate_exam_data)
        candidate_exam_instance = CandidateExam.get_detail_queryset(
            exam_backlog=True, candidate=True, q_filter=Q(pk=candidate_exam_instance.pk)
        ).first()
        response_data = CandidateExamListSerializer(candidate_exam_instance).data
        exam_instance.delete()  # type:ignore
        return Response(response_data)

    def get_exam_backlogs_with_candidate_detail(self, request):
        q_filter = get_exambacklog_q_filter(request)
        exam_backlog_queryset = (
            ExamBacklog.objects.filter(q_filter & Q(candidate_exam_examsbacklog__isnull=False) & Q(candidate_exam_examsbacklog__meta_status="active"))
            .prefetch_related(
                Prefetch(
                    "candidate_exam_examsbacklog",
                    queryset=CandidateExam.get_detail_queryset(exam_backlog=True, candidate=True, is_organization_filter=True),
                )
            )
            .distinct()
            .order_by("-id")
        )

        exam_backlog_queryset = [
            exam_backlog_instance
            for exam_backlog_instance in exam_backlog_queryset
            if exam_backlog_instance.candidate_exam_examsbacklog.exists()  # type:ignore
        ]

        exam_backlog_list = ExamBacklogWithCandidateDetailsSerializer(exam_backlog_queryset, many=True).data

        return Response(exam_backlog_list, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="answers")
    def candidate_exam_answers(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        candidate_exam_backlog_question_instance = get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id, get_answers=True)
        data = CandidateExamWithAnswersDetailSerializer(candidate_exam_backlog_question_instance, context={"get_answers": True}).data
        return Response(data, status=status.HTTP_200_OK)

    def send_exam_link_to_users(self, request, *args, **kwargs):
        candidate_exam_ids = request.data["candidate_exam_ids"]
        if not len(candidate_exam_ids):
            return make_error_response(message="Candidate Exam ID's are required.")
        CandidateExamNinja().send_exam_invitation_link(candidate_exam_ids)
        return Response({"message": "Exam invitation emails sent successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="retry-hint")
    def candidate_exam_retry_hint(self, request, *args, **kwargs):
        question_backlog_id = request.query_params.get("question_backlog_id", None)
        if question_backlog_id is None:
            return make_error_response(message="Question Backlog id is required")
        candidate_exam_id = int(self.kwargs["pk"])
        candidate_exam_instance = CandidateExam.objects.filter(id=candidate_exam_id).first()
        if not candidate_exam_instance:
            return make_error_response(message="Candidate Exam not found")
        data = CandidateExamNinja().get_retry_hint_for_candidate_exam(
            question_backlog_id=int(question_backlog_id), candidate_exam_id=candidate_exam_id
        )
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="submit")
    @transaction.atomic
    def candidate_exam_submission(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        data = CandidateExamNinja().submit_candidate_exam(candidate_exam_id)
        return Response({"message": data["message"]}, status=data["status"])


# ---------------------------------------------------------------------------- #
#                            ATTEMPT CANDIDATE EXAM                            #
# ---------------------------------------------------------------------------- #


class AttemptCandidateExamAPI(views.APIView):

    def post(self, request, *args, **kwargs):
        user_roles = get_current_user().get_user_role_slugs  # type:ignore
        if any(role != "candidate" for role in user_roles):
            return make_error_response(message="Exam not allowed to the requested user.")
        request_data = request.data
        response_data = CandidateExamNinja().attempt_candidate_exam(request_data)
        return Response(response_data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------- #
#                             CANDIDATE EXAM ANSWER                            #
# ---------------------------------------------------------------------------- #


class CandidateExamAnswerViewset(viewsets.ModelViewSet):
    queryset = (
        CandidateExamAnswer.objects.all().select_related("exam_backlog_question", "exam_backlog_question_choice").prefetch_related("answer_files")
    )
    serializer_class = CandidateExamAnswerSerializer
    pagination_class = None
    http_method_names = ["get", "post"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = json.loads(request.data["data"])
        candidate_exam_id = request_data.pop("candidate_exam")
        request_data = request_data.pop("answers")
        CandidateExamNinja().save_candidate_exam_answers(candidate_exam_id, request_data, request)
        return Response(status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------- #
#                                 EXAM BACKLOGS                                #
# ---------------------------------------------------------------------------- #


class ExamBacklogAPI(views.APIView):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        exam_id = request.data.get("exam")
        if not exam_id:
            return make_error_response(message="Exam ID is required.")
        exam_instance = Exam.get_detail_queryset(all=True, q_filter=Q(id=exam_id)).first()
        if not exam_instance:
            return make_error_response(message="Exam not found.")
        exam_data = ExamDetailSerializerForBacklogs(exam_instance).data
        exam_backlogs = ExamBacklogsNinja(exam_data=exam_data)  # type:ignore
        exam_backlog_id = exam_backlogs.create_backlogs()
        return Response({"exam_backlog_id": exam_backlog_id}, status=status.HTTP_200_OK)


class ExamBacklogAnswerKeyAPI(views.APIView):

    def get(self, request, *args, **kwargs):
        exam_backlog = (
            ExamBacklog.objects.filter(id=self.kwargs["pk"])
            .prefetch_related(
                Prefetch(
                    "backlog_questions",
                    queryset=ExamBacklogQuestion.objects.prefetch_related(
                        Prefetch("backlog_choices", queryset=ExamBacklogQuestionChoice.objects.filter(is_correct=True))
                    ),
                )
            )
            .first()
        )

        response_list = [
            {
                "question_backlog_id": question.id,
                "question_backlog_title": question.title,
                "correct_choices": ExamBacklogQuestionChoiceForKeySerializer(question.backlog_choices.all(), many=True).data,
            }
            for question in exam_backlog.backlog_questions.all()  # type:ignore
            if question.backlog_choices.exists()
        ]

        return Response(data=response_list, status=status.HTTP_200_OK)


class AssignExaminersAPI(views.APIView):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        request_data = request.data
        exam_backlog_id = request_data.get("exam_backlog_id")
        examiners_details_list = request_data.get("examiners")
        if not exam_backlog_id:
            return make_error_response(message="Exam Backlog ID is required.")
        if not examiners_details_list:
            return make_error_response(message="Examiners are required.")
        CandidateExamNinja().assign_examiners_to_exam_backlog(exam_backlog_id, examiners_details_list)
        return Response({"message": "Examiners Assigned Successfully"})
