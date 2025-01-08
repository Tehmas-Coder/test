import json

from django.db import transaction
from django.db.models import Prefetch, Q
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializerForBacklogs
from apps.exam_public.custom.candidate_exam_classes import CandidateExamNinja
from apps.exam_public.custom.exam_backlogs_classes import ExamBacklogsNinja
from apps.exam_public.filters.candidate_exam_filters import CandidateExamFilterBackend
from apps.exam_public.filters.candidate_filters import CandidateFilterBackend
from apps.exam_public.filters.exam_backlog_filters import get_exambacklog_q_filter
from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.helpers.exam_status_webhook import (
    send_exam_status_to_student_apply_webhook,
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
    CandidateExamAnswerMedia,
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
from apps.questionbank.serializers.media_serializers import MediaBulkCreateSerializer
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
    queryset = CandidateExam.get_detail_queryset(exam_backlog=True, candidate=True)
    serializer_class = CandidateExamEditSerializer
    http_method_names = ["get", "post", "patch"]
    filter_backends = [CandidateExamFilterBackend]

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateExamListSerializer
        return super().get_serializer_class()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = request.data
        exam_id = request_data.get("exam")
        if exam_id:
            request_data.pop("exam")
            exam_instance = Exam.get_detail_queryset(all=True, q_filter=Q(id=exam_id)).first()
            # * Creating Backlogs for Exam
            exam_data = ExamDetailSerializerForBacklogs(exam_instance).data
            exam_backlogs = ExamBacklogsNinja(exam_data=exam_data)  # type:ignore
            exambacklog_id = exam_backlogs.create_backlogs()
        else:
            exambacklog_id = request_data.get("exam_backlog")

        # * Assigning Exam to Candidates
        request_data["exam_backlog"] = exambacklog_id
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        candidate_exam_instances = serializer.save()

        # * Fetching newly created instances
        created_candidate_exam_instances = self.get_queryset().order_by("-created_at")[: len(candidate_exam_instances)]
        created_candidate_exam_instances = sorted(created_candidate_exam_instances, key=lambda instance: instance.id)
        response_data = CandidateExamListSerializer(created_candidate_exam_instances, many=True).data

        # * Sending Exam Invitation Emails
        if request_data.get("is_send_invitation_emails"):
            candidate_exam_ids = [one_candidate_exam["id"] for one_candidate_exam in response_data]
            CandidateExamNinja().send_exam_invitation_link(candidate_exam_ids)

        return Response(response_data, status=status.HTTP_201_CREATED)

    def retrieve(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        candidate_exam_backlog_question_instance = CandidateExamNinja().get_candidate_exam(candidate_exam_id)
        data = CandidateExamDetailSerializer(
            candidate_exam_backlog_question_instance, context={"get_retry_hints": candidate_exam_backlog_question_instance.is_preparatory}  # type: ignore
        ).data
        return Response(data, status=status.HTTP_200_OK)

    def get_exam_backlogs_with_candidate_detail(self, request):
        q_filter = get_exambacklog_q_filter(request)
        exam_backlog_list = ExamBacklogWithCandidateDetailsSerializer(
            ExamBacklog.objects.filter(q_filter)
            .prefetch_related(Prefetch("candidate_exam_examsbacklog", queryset=CandidateExam.get_detail_queryset(exam_backlog=True, candidate=True)))
            .distinct(),
            many=True,
        ).data

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
    def candidate_exam_submission(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        data = CandidateExamNinja().submit_candidate_exam(candidate_exam_id)
        return Response({"message": data["message"]}, status=data["status"])


# ---------------------------------------------------------------------------- #
#                            ATTEMPT CANDIDATE EXAM                            #
# ---------------------------------------------------------------------------- #


class AttemptCandidateExamAPI(views.APIView):

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        request_data = request.data
        response_data = CandidateExamNinja().attempt_candidate_exam(request_data)
        return Response(response_data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------- #
#                             CANDIDATE EXAM ANSWER                            #
# ---------------------------------------------------------------------------- #


class CandidateExamAnswerViewset(viewsets.ModelViewSet):
    queryset = (
        CandidateExamAnswer.objects.all()
        .select_related(
            "exam_backlog_question",
            "exam_backlog_question_choice",
        )
        .prefetch_related("answer_files")
    )
    serializer_class = CandidateExamAnswerSerializer
    pagination_class = None
    http_method_names = ["get", "post"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = json.loads(request.data["data"])
        candidate_exam_id = request_data.pop("candidate_exam")
        request_data = request_data.pop("answers")

        # * Extract media for answers
        answer_media_hashmap = {}
        for answer in request_data:
            exam_backlog_question_id = answer["exam_backlog_question"]
            answer_files = answer.pop("answer_files", [])

            if len(answer_files):
                if exam_backlog_question_id not in answer_media_hashmap:
                    answer_media_hashmap[exam_backlog_question_id] = {}
                answer_media_hashmap[exam_backlog_question_id] = {"exam_backlog_question_id": exam_backlog_question_id, "files": []}
                for key in answer_files:
                    file = request.FILES.get(key)
                    if file:
                        answer_media_hashmap[exam_backlog_question_id]["files"].append(file)

        exam_backlog_question_choices_ids = [
            one_dict["exam_backlog_question_choice"] for one_dict in request_data if one_dict["exam_backlog_question_choice"] != None
        ]

        exam_backlog_question_choices_instances = list(
            ExamBacklogQuestionChoice.objects.filter(id__in=exam_backlog_question_choices_ids).values("id", "title")
        )

        exam_backlog_question_choices_hashmap = {one_dict["id"]: one_dict["title"] for one_dict in exam_backlog_question_choices_instances}

        CandidateExamAnswer.objects.bulk_create(
            [
                CandidateExamAnswer(
                    candidate_exam_id=candidate_exam_id,
                    exam_backlog_question_id=one_dict["exam_backlog_question"],
                    exam_backlog_question_choice_id=one_dict.get("exam_backlog_question_choice"),
                    exam_backlog_question_choice_title=(
                        exam_backlog_question_choices_hashmap[one_dict.get("exam_backlog_question_choice")]
                        if one_dict.get("exam_backlog_question_choice") != None
                        else None
                    ),
                    answer_text=one_dict.get("answer_text"),
                    is_attempted=True,
                )
                for one_dict in request_data
            ]
        )

        newly_created_queryset = list(
            CandidateExamAnswer.objects.all().values_list("id", "exam_backlog_question_id").order_by("-created_at")[: len(request_data)]
        )

        CandidateExam.objects.filter(id=candidate_exam_id).update(exam_status="attempted")
        candidate_exam_instance = CandidateExam.objects.filter(id=candidate_exam_id).first()
        if candidate_exam_instance.candidate.organization and candidate_exam_instance.candidate.organization.token:  # type: ignore
            send_exam_status_to_student_apply_webhook(candidate_exam_instance)

        for one_dict in newly_created_queryset:
            candidate_exam_answer_id = one_dict[0]
            exam_backlog_question_id = one_dict[1]
            if exam_backlog_question_id in answer_media_hashmap:
                answer_media_hashmap[exam_backlog_question_id]["candidate_exam_answer"] = candidate_exam_answer_id

        for key, value in answer_media_hashmap.items():
            media_data = {"files": value["files"]}
            media_serializer = MediaBulkCreateSerializer(data=media_data)
            media_serializer.is_valid(raise_exception=True)
            media_instances = media_serializer.save()
            value.pop("files")
            value["media_ids"] = [one_instance.id for one_instance in media_instances]

        CandidateExamAnswerMedia.objects.bulk_create(
            [
                CandidateExamAnswerMedia(
                    candidate_exam_answer_id=value["candidate_exam_answer"],
                    media_id=one_media_id,
                )
                for key, value in answer_media_hashmap.items()
                for one_media_id in value["media_ids"]
            ]
        )
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
