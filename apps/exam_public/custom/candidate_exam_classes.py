import json
import random

from cryptography.fernet import Fernet
from decouple import config
from django.db.models import F, Q

from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionRetryHint,
)
from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamRetryhint,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_retryhint_serializer import (
    ExamBacklogQuestionRetryHintSerializer,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import (
    get_encryption_key,
    make_error_response,
    remove_extra_underscore_from_key_names,
)


class CandidateExamNinja:

    def __init__(self) -> None:
        pass

    def get_candidate_exam(self, candidate_exam_id):
        logged_in_user_id = get_current_user().id  # type:ignore

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
                ResponseMiddleware.return_now(make_error_response(message="Invalid token"))

        # * IF ROLES ARE ( Organization Roles and Candidate )
        logged_in_user_roles = get_current_user().get_user_role_slugs  # type:ignore
        if len(logged_in_user_roles):
            if "candidate" in logged_in_user_roles:
                candidate_exam_filter_data = {
                    "id": candidate_exam_id,
                    "candidate__user__id": logged_in_user_id,
                }

                if not CandidateExam.objects.filter(**candidate_exam_filter_data).exists():
                    ResponseMiddleware.return_now(make_error_response(message="Exam not allowed to this candidate"))
        return get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id)

    def send_exam_invitation_link(self, candidate_exam_ids: list):
        logged_in_user = get_current_user()

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
        organization_id = None if logged_in_user.is_superuser else get_current_user_organization()  # type:ignore
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
                ResponseMiddleware.return_now(
                    make_error_response(message=f"Unable to send exam link to user: {one_candidate_detail['candidate_email']}")
                )

    def get_retry_hint_for_candidate_exam(self, question_backlog_id: int, candidate_exam_id: int):
        candidate_exam_retryhints_ids = CandidateExamRetryhint.objects.filter(
            candidate_exam_id=candidate_exam_id, exam_backlog_question_id=question_backlog_id
        ).values_list("exam_backlog_question_retry_hint", flat=True)
        exam_backlog_question = ExamBacklogQuestion.objects.filter(id=question_backlog_id).first()
        if not exam_backlog_question:
            ResponseMiddleware.return_now(make_error_response(message="Question not found"))
        if len(candidate_exam_retryhints_ids) >= exam_backlog_question.max_retries:  # type:ignore
            ResponseMiddleware.return_now(make_error_response(message="Max retries limit reached."))
        else:
            exam_backlog_question_retryhints_instances = list(
                ExamBacklogQuestionRetryHint.get_detail_queryset(media=True, q_filter=Q(exam_backlog_question=exam_backlog_question)).exclude(
                    id__in=candidate_exam_retryhints_ids
                )
            )
            if not len(exam_backlog_question_retryhints_instances):
                ResponseMiddleware.return_now(make_error_response(message="No More Retries."))
            random.shuffle(exam_backlog_question_retryhints_instances)
            retry_hint_instance = exam_backlog_question_retryhints_instances[0]
            CandidateExamRetryhint.objects.create(
                candidate_exam_id=candidate_exam_id, exam_backlog_question=exam_backlog_question, exam_backlog_question_retry_hint=retry_hint_instance
            )
            return ExamBacklogQuestionRetryHintSerializer(retry_hint_instance).data
