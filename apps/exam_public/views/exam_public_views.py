import json
import random
from re import sub

from cryptography.fernet import Fernet
from decouple import config
from django.db.models import F, Prefetch, Q, Sum
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializerForBacklogs
from apps.exam_public.classes.exam_backlogs_helper import ExamBacklogsNinja
from apps.exam_public.filters.candidate_exam_filters import CandidateExamFilterBackend
from apps.exam_public.filters.candidate_filters import CandidateFilterBackend
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklog,
    ExamBacklogQuestion,
    ExamBacklogQuestionChoice,
    ExamBacklogQuestionChoiceMedia,
    ExamBacklogQuestionCountry,
    ExamBacklogQuestionMedia,
    ExamBacklogQuestionRetryHint,
    ExamBacklogQuestionRetryHintMedia,
)
from apps.exam_public.models.exam_public_models import (
    Candidate,
    CandidateExam,
    CandidateExamAnswer,
    CandidateExamAnswerMedia,
    CandidateExamRetryhint,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_serializer import (
    ExamBacklogQuestionChoiceForKeySerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_retryhint_serializer import (
    ExamBacklogQuestionRetryHintSerializer,
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
from apps.exam_scoring.models.exam_score_models import (
    CandidateExamSectionScore,
    CandidateExamSubSectionScore,
)
from apps.organization.models.organization_models import OrganizationUser
from apps.questionbank.serializers.media_serializers import MediaBulkCreateSerializer
from apps.user.models import BaseUser, Role, RolePermission
from utils.email_notifications import EmailNotification
from utils.rna_utils import (
    color_print,
    debug_print,
    get_encryption_key,
    make_error_response,
    remove_extra_underscore_from_key_names,
)

# --------------------------------- CANDIDATE -------------------------------- #


class CandidateViewSet(viewsets.ModelViewSet):
    queryset = (
        Candidate.objects.all()
        .select_related(
            "user",
            "user__country",
            "user__profile_picture",
            "organization",
            "organization__country",
        )
        .prefetch_related(
            Prefetch(
                "user__roles",
                queryset=Role.objects.all().prefetch_related(
                    Prefetch("role_permissions", queryset=RolePermission.objects.all().select_related("permission"))
                ),
            ),
        )
    )
    serializer_class = CandidateSerializer
    filter_backends = [CandidateFilterBackend]
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
            "candidate__organization",
            "candidate__organization__country",
        )
        .prefetch_related(
            Prefetch(
                "candidate__user__roles",
                queryset=Role.objects.all().prefetch_related(
                    Prefetch("role_permissions", queryset=RolePermission.objects.all().select_related("permission"))
                ),
            ),
        )
    )

    serializer_class = CandidateExamEditSerializer
    http_method_names = ["get", "post", "patch"]
    filter_backends = [CandidateExamFilterBackend]

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
        exam_backlogs = ExamBacklogsNinja(exam_data=exam_data)  # type:ignore
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
        candidate_exam_id = self.kwargs["pk"]
        logged_in_user: BaseUser = self.request.user  # type:ignore
        logged_in_user_id = logged_in_user.id  # type:ignore

        candidate_exam_id = self.kwargs["pk"]
        try:
            candidate_exam_id = int(candidate_exam_id)
        except:
            try:
                token = candidate_exam_id[len("token=") :]
                key = get_encryption_key()
                cipher = Fernet(key)
                decrypted_data = json.loads(cipher.decrypt(token).decode())
                candidate_exam_id = decrypted_data["candidate_exam_id"]
            except:
                return make_error_response(message="Invalid token")

        # * IF ROLES ARE ( Organization Roles and Candidate )
        logged_in_user_roles = logged_in_user.get_user_role_slugs  # type:ignore
        if len(logged_in_user_roles):
            if "candidate" in logged_in_user_roles:
                candidate_exam_filter_data = {
                    "id": candidate_exam_id,
                    "candidate__user__id": logged_in_user_id,
                }

                if not CandidateExam.objects.filter(**candidate_exam_filter_data).exists():
                    return Response(
                        data={
                            "Status": "failed",
                            "message": f"Exam not allowed to this candidate",
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        candidate_exam_data = (
            CandidateExam.objects.filter(id=candidate_exam_id)
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

        question_instances_total_marks = ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list).aggregate(
            total_score=Sum("total_marks")
        )["total_score"]
        CandidateExam.objects.filter(id=candidate_exam_id).update(
            total_obtainable_marks=question_instances_total_marks if question_instances_total_marks != None else 0
        )

        candidate_exam_backlog_question_instance = self.queryset.filter(id=candidate_exam_id).prefetch_related(
            Prefetch(
                "exam_backlog__backlog_questions",
                queryset=ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list)
                .select_related(
                    "type",
                    "measuring_unit",
                    "difficulty_level",
                    "section_backlog",
                    "section_backlog__measuring_unit",
                    "subsection_backlog",
                    "subsection_backlog__measuring_unit",
                )
                .prefetch_related(
                    "backlog_tags",
                    "backlog_attempt_responses",
                    Prefetch(
                        "exambacklogquestioncountry_set",
                        queryset=ExamBacklogQuestionCountry.objects.all().select_related("country"),
                    ),
                    Prefetch(
                        "exambacklogquestionmedia_set",
                        queryset=ExamBacklogQuestionMedia.objects.all().select_related("media"),
                    ),
                    Prefetch(
                        "backlog_choices",
                        queryset=ExamBacklogQuestionChoice.objects.all().prefetch_related(
                            Prefetch(
                                "exambacklogquestionchoicemedia_set", queryset=ExamBacklogQuestionChoiceMedia.objects.all().select_related("media")
                            )
                        ),
                    ),
                    Prefetch(
                        "backlog_retry_hints",
                        queryset=ExamBacklogQuestionRetryHint.objects.all().prefetch_related(
                            Prefetch(
                                "exambacklogquestionretryhintmedia_set",
                                queryset=ExamBacklogQuestionRetryHintMedia.objects.all().select_related("media"),
                            )
                        ),
                    ),
                ),
            )
        )[0]

        data = CandidateExamDetailSerializer(
            candidate_exam_backlog_question_instance, context={"get_retry_hints": candidate_exam_backlog_question_instance.is_preparatory}
        ).data

        return Response(data, status=status.HTTP_200_OK)

    def get_exam_backlogs_with_candidate_detail(self, request):
        name = request.query_params.get("name")
        education_levels = request.query_params.get("education_levels")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        q_filter = Q()

        if name:
            name = str(name)
            q_filter &= Q(name__icontains=name)

        if education_levels:
            education_levels = json.loads(education_levels)
            education_levels = [int(id) for id in education_levels]
            q_filter &= Q(education_level_id__in=education_levels)

        if start_date and not end_date:
            start_date = str(start_date)
            q_filter &= Q(candiate_exam_examsbacklog__start_datetime__date=start_date)

        if end_date and not start_date:
            end_date = str(end_date)
            q_filter &= Q(candiate_exam_examsbacklog__end_datetime__date=end_date)

        if start_date and end_date:
            start_date = str(start_date)
            end_date = str(end_date)
            q_filter &= Q(candiate_exam_examsbacklog__start_datetime__date__range=[start_date, end_date])

        exam_backlog_list = ExamBacklogWithCandidateDetailsSerializer(
            ExamBacklog.objects.filter(q_filter)
            .prefetch_related(
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
                        "candidate__organization",
                        "candidate__organization__country",
                    )
                    .prefetch_related(
                        Prefetch(
                            "candidate__user__roles",
                            queryset=Role.objects.all().prefetch_related(
                                Prefetch("role_permissions", queryset=RolePermission.objects.all().select_related("permission"))
                            ),
                        ),
                    ),
                )
            )
            .distinct(),
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
                .select_related(
                    "type",
                    "measuring_unit",
                    "difficulty_level",
                    "section_backlog",
                    "section_backlog__measuring_unit",
                    "subsection_backlog",
                    "subsection_backlog__measuring_unit",
                )
                .prefetch_related(
                    "backlog_tags",
                    "backlog_attempt_responses",
                    Prefetch(
                        "exambacklogquestioncountry_set",
                        queryset=ExamBacklogQuestionCountry.objects.all().select_related("country"),
                    ),
                    Prefetch(
                        "exambacklogquestionmedia_set",
                        queryset=ExamBacklogQuestionMedia.objects.all().select_related("media"),
                    ),
                    Prefetch(
                        "backlog_choices",
                        queryset=ExamBacklogQuestionChoice.objects.all().prefetch_related(
                            Prefetch(
                                "exambacklogquestionchoicemedia_set", queryset=ExamBacklogQuestionChoiceMedia.objects.all().select_related("media")
                            )
                        ),
                    ),
                    Prefetch(
                        "backlog_retry_hints",
                        queryset=ExamBacklogQuestionRetryHint.objects.all().prefetch_related(
                            Prefetch(
                                "exambacklogquestionretryhintmedia_set",
                                queryset=ExamBacklogQuestionRetryHintMedia.objects.all().select_related("media"),
                            )
                        ),
                    ),
                    Prefetch(
                        "question_answers",
                        CandidateExamAnswer.objects.all()
                        .select_related(
                            "exam_backlog_question_choice",
                        )
                        .prefetch_related(
                            "answer_files",
                            Prefetch(
                                "exam_backlog_question_choice__exambacklogquestionchoicemedia_set",
                                queryset=ExamBacklogQuestionChoiceMedia.objects.all().select_related("media"),
                            ),
                        ),
                    ),
                ),
            )
        )[0]

        data = CandidateExamWithAnswersDetailSerializer(candidate_exam_backlog_question_instance, context={"get_answers": True}).data
        return Response(data, status=status.HTTP_200_OK)

    def send_exam_link_to_users(self, request, *args, **kwargs):
        logged_in_user = request.user
        candidate_exam_ids = request.data["candidate_exam_ids"]
        if not len(candidate_exam_ids):
            return Response({"message": "Candidate Exam ID's required."}, status=status.HTTP_400_BAD_REQUEST)

        candidate_exam_detail_queryset = remove_extra_underscore_from_key_names(
            list(
                CandidateExam.objects.filter(id__in=candidate_exam_ids)
                .annotate(
                    first_name=F("candidate__user__first_name"),
                    last_name=F("candidate__user__last_name"),
                    exam=F("exam_backlog__name"),
                )
                .values()
            )
        )
        organization_id = None
        if not request.user.is_superuser:
            organization_id = OrganizationUser.objects.filter(user_id=logged_in_user.id).values("organization").first()["organization"]  # type:ignore
        for one_candidate_detail in candidate_exam_detail_queryset:
            key = get_encryption_key()
            cipher = Fernet(key)
            candidate_exam_id = one_candidate_detail["id"]

            data_to_encrypt = {
                "email": one_candidate_detail["candidate_email"],
                "candidate_exam_id": candidate_exam_id,
                "organization_id": organization_id,
            }
            encrypted_data = cipher.encrypt(json.dumps(data_to_encrypt).encode())

            token_data = encrypted_data.decode("utf-8")
            token_data = f"{token_data}"
            url = config("QB_PUBLIC_FE_URL")
            final_url = f"{url}exam/get?token={token_data}"
            send_email_data_dict = send_email_data_dict = {
                "first_name": one_candidate_detail["first_name"] or "",
                "last_name": one_candidate_detail["last_name"] or "",
                "email": one_candidate_detail["candidate_email"],
                "exam": one_candidate_detail["exam"],
                "exam_duration": one_candidate_detail.get("exam_duration", ""),
                "start_datetime": one_candidate_detail.get("start_datetime", "").strftime("%Y-%m-%d %H:%M:%S"),
                "end_datetime": one_candidate_detail.get("end_datetime", "").strftime("%Y-%m-%d %H:%M:%S"),
                "url": final_url,
            }
            email_notification_ninja = EmailNotification(send_email_data_dict)
            if not email_notification_ninja.send_exam_link():
                return Response(
                    data={
                        "Status": "failed",
                        "message": f"Unable to send exam link to user: {one_candidate_detail['candidate_email']}",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            del email_notification_ninja

        return Response({"message": "Exam invitation emails sent successfully"}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["get"], url_path="retry-hint")
    def candidate_exam_retry_hint(self, request, *args, **kwargs):
        question_backlog_id = request.query_params.get("question_backlog_id", None)
        if question_backlog_id is None:
            return make_error_response(message="Question Backlog id is required")

        question_backlog_id = int(question_backlog_id)
        candidate_exam_id = int(self.kwargs["pk"])
        candidate_exam_retryhints_ids = CandidateExamRetryhint.objects.filter(
            candidate_exam_id=candidate_exam_id, exam_backlog_question_id=question_backlog_id
        ).values_list("exam_backlog_question_retry_hint", flat=True)
        exam_backlog_question = ExamBacklogQuestion.objects.get(id=question_backlog_id)
        if len(candidate_exam_retryhints_ids) >= exam_backlog_question.max_retries:
            return make_error_response(message="Max retries limit reached.")
        else:
            exam_backlog_question_retryhints_instances = list(
                ExamBacklogQuestionRetryHint.objects.filter(exam_backlog_question=exam_backlog_question)
                .prefetch_related(
                    "exambacklogquestionretryhintmedia_set",
                    "exambacklogquestionretryhintmedia_set__media",
                )
                .exclude(id__in=candidate_exam_retryhints_ids)
            )
            if not len(exam_backlog_question_retryhints_instances):
                return make_error_response(message="No More Retries.")
            random.shuffle(exam_backlog_question_retryhints_instances)
            retry_hint_instance = exam_backlog_question_retryhints_instances[0]
            CandidateExamRetryhint.objects.create(
                candidate_exam_id=candidate_exam_id, exam_backlog_question=exam_backlog_question, exam_backlog_question_retry_hint=retry_hint_instance
            )
            data = ExamBacklogQuestionRetryHintSerializer(retry_hint_instance).data
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"], url_path="submit")
    def candidate_exam_submission(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs["pk"]
        candidate_exam_answers_queryset = (
            CandidateExamAnswer.objects.filter(candidate_exam_id=candidate_exam_id)
            .select_related(
                "exam_backlog_question_choice",
                "exam_backlog_question",
            )
            .annotate(penalty_score=Sum("exam_backlog_question__question_fetched_retry_hints__penalty_score"))
        )

        # * Scoring objective type questions answers if the choice is correct then answer is also marked as correct and scored as positive, if the choice is incorrect and weight is 0 then answer is marked as 0 and if the wheigt is negative then marked as negative socre and at the end if user took any retry hints while solving then it minus the sum of penalty scores from the obtained score
        CandidateExamAnswer.objects.bulk_update(
            [
                CandidateExamAnswer(
                    id=one_candidate_exam_answer.id,  # type:ignore
                    is_correct=one_candidate_exam_answer.exam_backlog_question_choice.is_correct,
                    score=(
                        (
                            float(
                                (one_candidate_exam_answer.exam_backlog_question_choice.weight / 100)
                                * one_candidate_exam_answer.exam_backlog_question.total_marks
                            )
                            if one_candidate_exam_answer.exam_backlog_question_choice.is_correct
                            else (
                                -float(
                                    (one_candidate_exam_answer.exam_backlog_question_choice.weight / 100)
                                    * one_candidate_exam_answer.exam_backlog_question.total_marks
                                )
                                if one_candidate_exam_answer.exam_backlog_question_choice.is_negative_weight
                                else 0
                            )
                        )
                        - float((one_candidate_exam_answer.penalty_score or 0))  # type: ignore
                    ),
                )
                for one_candidate_exam_answer in candidate_exam_answers_queryset
                if one_candidate_exam_answer.exam_backlog_question_choice
            ],
            fields=["is_correct", "score"],
        )

        # * Creating Candidate Exam Answer transactions with score set to 0 for questions which are not even attempted.

        # Fetching the total questions assigned to the candidate according to his country and global questions
        candidate_exam_data = (
            CandidateExam.objects.filter(id=candidate_exam_id)
            .annotate(country_id=F("candidate__user__country_id"))
            .values(
                "country_id",
                "exam_backlog",
            )
            .first()
        )

        exam_question_backlog = list(
            ExamBacklogQuestion.objects.filter(exam_backlog_id=candidate_exam_data["exam_backlog"]).values("is_global", "id")  # type:ignore
        )
        is_global_exam_question_backlog_ids_list = [one_dict["id"] for one_dict in exam_question_backlog if one_dict["is_global"]]

        exam_question_backlog_ids = [one_dict["id"] for one_dict in exam_question_backlog if not one_dict["is_global"]]
        is_not_global_exam_question_backlog_ids_list: list = list(
            ExamBacklogQuestionCountry.objects.filter(
                exam_backlog_question_id__in=exam_question_backlog_ids,
                country_id=candidate_exam_data["country_id"],  # type:ignore
            ).values_list("exam_backlog_question", flat=True)
        )
        final_user_backlog_question_ids_list = is_global_exam_question_backlog_ids_list + is_not_global_exam_question_backlog_ids_list

        candidate_exam_answers_question_ids_list = list(
            CandidateExamAnswer.objects.filter(candidate_exam_id=candidate_exam_id).values_list("exam_backlog_question", flat=True)
        )

        unattempted_question_ids_list = list(set(set(final_user_backlog_question_ids_list) - set(candidate_exam_answers_question_ids_list)))

        # * Creating instances for unattempted questions
        CandidateExamAnswer.objects.bulk_create(
            [
                CandidateExamAnswer(
                    candidate_exam_id=candidate_exam_id,
                    exam_backlog_question_id=one_question_id,
                    is_attempted=False,
                    score=0,
                )
                for one_question_id in unattempted_question_ids_list
            ]
        )

        # * Creating Section and Subsection score models instances to store the sections and subsections scores of this Candidate Exam
        candidate_exam_questions_with_sections_and_subsections = ExamBacklogQuestion.objects.filter(
            id__in=final_user_backlog_question_ids_list, section_backlog__isnull=False
        )
        candidate_exam_questions_with_subsections = candidate_exam_questions_with_sections_and_subsections.filter(subsection_backlog__isnull=False)

        section_backlog_questions_details_hashmap = {}
        for one_candidate_exam_questions_with_section in candidate_exam_questions_with_sections_and_subsections:
            section_id = one_candidate_exam_questions_with_section.section_backlog_id  # type: ignore
            if section_id not in section_backlog_questions_details_hashmap:
                section_backlog_questions_details_hashmap[section_id] = {}
                section_backlog_questions_details_hashmap[section_id]["question_count"] = 0
                section_backlog_questions_details_hashmap[section_id]["total_obtainable_marks"] = 0
                section_backlog_questions_details_hashmap[section_id]["subsection_count"] = 0
            if one_candidate_exam_questions_with_section.subsection_backlog_id == None:  # type: ignore
                section_backlog_questions_details_hashmap[section_id]["question_count"] = (
                    section_backlog_questions_details_hashmap[section_id]["question_count"] + 1
                )
                section_backlog_questions_details_hashmap[section_id]["total_obtainable_marks"] = (
                    section_backlog_questions_details_hashmap[section_id]["total_obtainable_marks"]
                    + one_candidate_exam_questions_with_section.total_marks
                )

        subsection_backlog_questions_details_hashmap = {}
        for one_candidate_exam_questions_with_subsection in candidate_exam_questions_with_subsections:
            section_id = one_candidate_exam_questions_with_subsection.section_backlog_id  # type: ignore
            subsection_id = one_candidate_exam_questions_with_subsection.subsection_backlog_id  # type: ignore
            if subsection_id not in subsection_backlog_questions_details_hashmap:
                subsection_backlog_questions_details_hashmap[subsection_id] = {}
                subsection_backlog_questions_details_hashmap[subsection_id]["question_count"] = 0
                subsection_backlog_questions_details_hashmap[subsection_id]["total_obtainable_marks"] = 0
                section_backlog_questions_details_hashmap[section_id]["subsection_count"] = (
                    section_backlog_questions_details_hashmap[section_id]["subsection_count"] + 1
                )

            subsection_backlog_questions_details_hashmap[subsection_id]["question_count"] = (
                subsection_backlog_questions_details_hashmap[subsection_id]["question_count"] + 1
            )
            subsection_backlog_questions_details_hashmap[subsection_id]["total_obtainable_marks"] = (
                subsection_backlog_questions_details_hashmap[subsection_id]["total_obtainable_marks"]
                + one_candidate_exam_questions_with_subsection.total_marks
            )
            section_backlog_questions_details_hashmap[section_id]["total_obtainable_marks"] = (
                section_backlog_questions_details_hashmap[section_id]["total_obtainable_marks"]
                + one_candidate_exam_questions_with_subsection.total_marks
            )

        # * Now Creating the section_score instances
        CandidateExamSectionScore.objects.bulk_create(
            [
                CandidateExamSectionScore(
                    candidate_exam_id=candidate_exam_id,
                    section_backlog_id=one_section_backlog_id,
                    question_count=question_data_dict["question_count"],
                    total_obtainable_marks=question_data_dict["total_obtainable_marks"],
                    subsection_count=question_data_dict["subsection_count"],
                )
                for one_section_backlog_id, question_data_dict in section_backlog_questions_details_hashmap.items()  # type:ignore
            ]
        )

        # * Now Creating the subsection_score instances
        CandidateExamSubSectionScore.objects.bulk_create(
            [
                CandidateExamSubSectionScore(
                    candidate_exam_id=candidate_exam_id,
                    subsection_backlog_id=one_subsection_backlog_id,
                    question_count=question_data_dict["question_count"],
                    total_obtainable_marks=question_data_dict["total_obtainable_marks"],
                )
                for one_subsection_backlog_id, question_data_dict in subsection_backlog_questions_details_hashmap.items()  # type:ignore
            ]
        )

        # * Updating the exam status to submitted
        CandidateExam.objects.filter(id=candidate_exam_id).update(exam_status="submitted")

        return Response({"message": "Exam Submitted Successfully"}, status=status.HTTP_200_OK)


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
        request_data = json.loads(request.data["data"])
        candidate_exam_id = request_data.pop("candidate_exam")
        request_data = request_data.pop("answers")

        # * This is for the use case in which if the user haven't even attempted a single question and submitted that exam in that case the fron't end will request for the creation of candidate exama nswers but there will be none to store it will just pass the api.
        if not len(request_data):
            return Response(status=status.HTTP_201_CREATED)

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
                    exam_backlog_question_choice_id=one_dict["exam_backlog_question_choice"],
                    exam_backlog_question_choice_title=(
                        exam_backlog_question_choices_hashmap[one_dict["exam_backlog_question_choice"]]
                        if one_dict["exam_backlog_question_choice"] != None
                        else None
                    ),
                    answer_text=one_dict.get("answer_text", None),
                    is_attempted=True,
                )
                for one_dict in request_data
            ]
        )

        newly_created_queryset = list(
            CandidateExamAnswer.objects.all().values_list("id", "exam_backlog_question_id").order_by("-created_at")[: len(request_data)]
        )

        CandidateExam.objects.filter(id=candidate_exam_id).update(exam_status="attempted")

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
            for question in exam_backlog.backlog_questions.all()  # type:ignore
            if question.backlog_choices.exists()
        ]

        return Response(data=response_list, status=status.HTTP_200_OK)
