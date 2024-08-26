import json

from cryptography.fernet import Fernet
from decouple import config
from django.db.models import F, Prefetch
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializerForBacklogs
from apps.exam_public.classes.exam_backlogs_helper import ExamBacklogs
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklog,
    ExamBacklogQuestion,
    ExamBacklogQuestionChoice,
    ExamBacklogQuestionCountry,
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
from apps.exam_public.serializers.candiate_serializers import (
    CandidateDetailSerializer,
    CandidateSerializer,
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
from apps.lookups.serializers.media_serializers import MediaBulkCreateSerializer
from utils.email_notifications import EmailNotification
from utils.rna_utils import debug_print, get_encryption_key, make_error_response, remove_extra_underscore_from_key_names

# --------------------------------- CANDIDATE -------------------------------- #


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = (
        Candidate.objects.all()
        .select_related("user", "user__country", "user__profile_picture", "organization", "organization__country")
        .prefetch_related("user__roles")
    )
    serializer_class = CandidateSerializer
    # filter_backends = [CandidateFilterBackend]
    pagination_class = None
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return CandidateDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        if Candidate.objects.filter(
            user_id=request.data["user"],
            organization_id=request.data.get("organization", None),
        ).exists():
            return make_error_response(data=request.data, message="Candidate with this organization already exists.")

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
            "candidate__user__profile_picture",
        )
        .prefetch_related("candidate__user__roles")
    )

    serializer_class = CandidateExamEditSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch"]

    def get_serializer_class(self):
        if self.action == "list":
            return CandidateExamListSerializer
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

    def retrieve(self, request, *args, **kwargs):
        candidate_exam_data = (
            CandidateExam.objects.filter(id=self.kwargs["pk"])
            .annotate(country_id=F("candidate__user__country_id"))
            .values(
                "country_id",
                "exam_backlog",
            )
            .first()
        )

        if not candidate_exam_data:
            return make_error_response(message="The requested candidate exam data is not present")

        exam_question_backlog = list(
            ExamBacklogQuestion.objects.filter(exam_backlog_id=candidate_exam_data["exam_backlog"]).values("is_global", "id")
        )
        is_global_exam_question_backlog_ids_list = [one_dict["id"] for one_dict in exam_question_backlog if one_dict["is_global"]]

        exam_question_backlog_ids = [one_dict["id"] for one_dict in exam_question_backlog if not one_dict["is_global"]]
        is_not_global_exam_question_backlog_ids_list: list = list(
            ExamBacklogQuestionCountry.objects.filter(
                exam_backlog_question_id__in=exam_question_backlog_ids,
                country_id=candidate_exam_data["country_id"],
            ).values_list("exam_backlog_question", flat=True)
        )
        final_user_backlog_question_ids_list = is_global_exam_question_backlog_ids_list + is_not_global_exam_question_backlog_ids_list

        candidate_exam_backlog_question_instance = self.queryset.filter(id=self.kwargs["pk"]).prefetch_related(
            Prefetch(
                "exam_backlog__backlog_questions",
                queryset=ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list)
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
                    "exambacklogquestioncountry_set__country",
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
            )
        )[0]

        data = CandidateExamDetailSerializer(
            candidate_exam_backlog_question_instance, context={"get_retry_hints": candidate_exam_backlog_question_instance.is_preparatory}
        ).data

        return Response(data, status=status.HTTP_200_OK)

    def get_exam_backlogs_with_candidate_detail(self, request):
        exam_backlog_list = ExamBacklogWithCandidateDetailsSerializer(
            ExamBacklog.objects.all().prefetch_related(
                Prefetch(
                    "candiate_exam_examsbacklog",
                    queryset=CandidateExam.objects.all()
                    .select_related(
                        "exam_backlog",
                        "schedule",
                        "candidate",
                        "candidate__user",
                        "candidate__user__country",
                        "candidate__user__profile_picture",
                    )
                    .prefetch_related("candidate__user__roles"),
                )
            ),
            many=True,
        ).data

        return Response(exam_backlog_list, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="answers")
    def candidate_exam_answers(self, request, *args, **kwargs):
        candidate_exam_data = (
            CandidateExam.objects.filter(id=self.kwargs["pk"])
            .annotate(country_id=F("candidate__user__country_id"))
            .values(
                "country_id",
                "exam_backlog",
            )
            .first()
        )

        if not candidate_exam_data:
            return make_error_response(message="The requested candidate exam data is not present")

        exam_question_backlog = list(
            ExamBacklogQuestion.objects.filter(exam_backlog_id=candidate_exam_data["exam_backlog"]).values("is_global", "id")
        )
        is_global_exam_question_backlog_ids_list = [one_dict["id"] for one_dict in exam_question_backlog if one_dict["is_global"]]

        exam_question_backlog_ids = [one_dict["id"] for one_dict in exam_question_backlog if not one_dict["is_global"]]
        is_not_global_exam_question_backlog_ids_list: list = list(
            ExamBacklogQuestionCountry.objects.filter(
                exam_backlog_question_id__in=exam_question_backlog_ids,
                country_id=candidate_exam_data["country_id"],
            ).values_list("exam_backlog_question", flat=True)
        )
        final_user_backlog_question_ids_list = is_global_exam_question_backlog_ids_list + is_not_global_exam_question_backlog_ids_list

        candidate_exam_backlog_question_instance = self.queryset.filter(id=self.kwargs["pk"]).prefetch_related(
            Prefetch(
                "exam_backlog__backlog_questions",
                queryset=ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list)
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
                    "exambacklogquestioncountry_set__country",
                    Prefetch(
                        "question_answers",
                        CandidateExamAnswer.objects.all()
                        .select_related(
                            "exam_backlog_question_choice",
                        )
                        .prefetch_related(
                            "answer_files",
                            "exam_backlog_question_choice__exambacklogquestionchoicemedia_set",
                            "exam_backlog_question_choice__exambacklogquestionchoicemedia_set__media",
                        ),
                    ),
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
            )
        )[0]

        data = CandidateExamWithAnswersDetailSerializer(candidate_exam_backlog_question_instance, context={"get_answers": True}).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="submit")
    def candidate_exam_submission(self, request, *args, **kwargs):
        candidate_exam_answers_queryset = CandidateExamAnswer.objects.filter(candidate_exam_id=self.kwargs["pk"]).select_related(
            "exam_backlog_question_choice",
            "exam_backlog_question",
        )
        CandidateExamAnswer.objects.bulk_update(
            [
                CandidateExamAnswer(
                    id=one_candidate_exam_answer.id,
                    is_correct=True,
                    score=float(
                        (one_candidate_exam_answer.exam_backlog_question_choice.weight / 100)
                        * one_candidate_exam_answer.exam_backlog_question.total_marks
                    ),
                )
                for one_candidate_exam_answer in candidate_exam_answers_queryset
                if one_candidate_exam_answer.exam_backlog_question_choice
                if one_candidate_exam_answer.exam_backlog_question_choice.is_correct
            ],
            fields=["is_correct", "score"],
        )
        return Response({"message": "Exam Submitted Successfully"}, status=status.HTTP_200_OK)

    def send_exam_link_to_users(self, request, *args, **kwargs):
        candidate_exam_ids = request.data["candidate_exam_ids"]
        if not len(candidate_exam_ids):
            return Response({"message": "Candidate Exam ID's required."}, status=status.HTTP_400_BAD_REQUEST)

        candidate_exam_detail_queryset = remove_extra_underscore_from_key_names(
            list(
                CandidateExam.objects.filter(id__in=candidate_exam_ids)
                .annotate(
                    email=F("candidate__user__email"),
                    first_name=F("candidate__user__first_name"),
                    last_name=F("candidate__user__last_name"),
                    exam=F("exam_backlog__name"),
                )
                .values()
            )
        )
        for one_canidate_detail in candidate_exam_detail_queryset:
            key = get_encryption_key()
            cipher = Fernet(key)

            encryption_data = {"email": one_canidate_detail["email"]}
            encrypted_email = cipher.encrypt(json.dumps(encryption_data).encode())

            token_data = encrypted_email.decode("utf-8")
            url = config("PUBLIC_FE_URL")
            final_url = f"{url}exam?token={token_data}"
            send_email_data_dict = {
                "first_name": one_canidate_detail["first_name"],
                "last_name": one_canidate_detail["last_name"],
                "email": one_canidate_detail["email"],
                "exam": one_canidate_detail["exam"],
                "date": one_canidate_detail["date"].strftime("%Y-%m-%d"),
                "start_time": one_canidate_detail["start_time"].strftime("%H:%M:%S"),
                "end_time": one_canidate_detail["end_time"].strftime("%H:%M:%S"),
                "url": final_url,
            }
            email_notification_ninja = EmailNotification(send_email_data_dict)
            if not email_notification_ninja.send_exam_link():
                return Response(
                    data={
                        "Status": "failed",
                        "message": f"Exam link not sent to user: {one_canidate_detail['email']}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            del email_notification_ninja

        return Response(status=status.HTTP_200_OK)


# --------------------------- CANDIDATE EXAM ANSWER -------------------------- #
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

    def create(self, request, *args, **kwargs):
        request_data = request.data["data"]
        request_data = json.loads(request_data)

        # Extract media for answers
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

        CandidateExamAnswer.objects.bulk_create(
            [
                CandidateExamAnswer(
                    candidate_exam_id=one_dict["candidate_exam"],
                    exam_backlog_question_id=one_dict["exam_backlog_question"],
                    exam_backlog_question_choice_id=one_dict["exam_backlog_question_choice"],
                    answer_text=one_dict["answer_text"],
                )
                for one_dict in request_data
            ]
        )

        newly_created_queryset = list(
            CandidateExamAnswer.objects.all().values_list("id", "exam_backlog_question_id").order_by("-created_at")[: len(request_data)]
        )

        for one_dict in newly_created_queryset:
            candidate_exam_answer_id = one_dict[0]
            exam_backlog_question_id = one_dict[1]
            if exam_backlog_question_id in answer_media_hashmap:
                answer_media_hashmap[exam_backlog_question_id]["candidate_exam_answer"] = candidate_exam_answer_id
                answer_media_hashmap

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


# ------------------------- EXAM BACKLOG ANSWERS KEY ------------------------- #


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
            for question in exam_backlog.backlog_questions.all()
            if question.backlog_choices.exists()
        ]

        return Response(data=response_list, status=status.HTTP_200_OK)
