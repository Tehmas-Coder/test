import json
import random

from cryptography.fernet import Fernet
from decouple import config
from django.db.models import F, Q, Sum
from rest_framework import status
from rest_framework.response import Response

from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.helpers.exam_status_webhook import (
    send_exam_status_to_student_apply_webhook,
)
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionRetryHint,
)
from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamAnswer,
    CandidateExamRetryhint,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_retryhint_serializer import (
    ExamBacklogQuestionRetryHintSerializer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamDetailSerializer,
)
from apps.exam_scoring.models.exam_scoring_models import (
    CandidateExamSectionScore,
    CandidateExamSubSectionScore,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.email_notifications import EmailNotification
from utils.rna_utils import (
    decrypt_message,
    encrypt_message,
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

    def submit_candidate_exam(self, candidate_exam_id: int) -> dict:
        candidate_exam_instance = CandidateExam.objects.filter(id=candidate_exam_id).first()
        if not candidate_exam_instance:
            ResponseMiddleware.return_now(make_error_response(message="Candidate Exam not found"))
        if candidate_exam_instance.exam_status == "submitted":  # type:ignore
            ResponseMiddleware.return_now(make_error_response(message="Exam already submitted"))

        self.__mark_objective_type_questions(candidate_exam_id)
        user_backlog_all_question_ids_list = get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id, fetch_only_question_ids=True)
        self.__mark_unattempted_questions(candidate_exam_id, user_backlog_all_question_ids_list)  # type:ignore
        self.__candidate_exam_section_and_subsection_scores_instances_creation(candidate_exam_id, user_backlog_all_question_ids_list)  # type:ignore
        message = "Exam Submitted Successfully"
        response_status = status.HTTP_200_OK

        # * Updating the exam status to submitted
        candidate_exam_instance.exam_status = "submitted"  # type:ignore
        candidate_exam_instance.save()  # type:ignore
        candidate_exam_instance.refresh_from_db()  # type:ignore
        if candidate_exam_instance.candidate.organization and candidate_exam_instance.candidate.organization.token:  # type: ignore
            if not send_exam_status_to_student_apply_webhook(candidate_exam_instance):
                message = message + " but failed to send exam status through webhook"
                response_status = status.HTTP_307_TEMPORARY_REDIRECT

        return {"message": message, "status": response_status}

    def attempt_candidate_exam(self, request_data: dict) -> dict:
        response_data = {}

        if "key" not in request_data:
            response_data = self.__set_response_data_for_attempt_candidate_exam_when_key_not_present(request_data, response_data)
        else:
            response_data = self.__set_response_data_for_attempt_candidate_exam_when_key_present(request_data, response_data)

        return response_data

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __mark_objective_type_questions(self, candidate_exam_id: int) -> None:
        """
        - This function scores objective type questions answers if the choice is correct then answer is also marked as correct and scored as positive,
        - If the choice is incorrect and weight is 0 then answer is marked as 0 and if the weight is negative then marked as negative score
        - At the end if user took any retry hints while solving then it minus the sum of penalty scores from the obtained score
        """

        candidate_exam_answers_queryset = (
            CandidateExamAnswer.objects.filter(candidate_exam_id=candidate_exam_id)
            .select_related(
                "exam_backlog_question_choice",
                "exam_backlog_question",
            )
            .annotate(penalty_score=Sum("exam_backlog_question__question_fetched_retry_hints__penalty_score"))
        )

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

    def __mark_unattempted_questions(self, candidate_exam_id: int, user_backlog_all_question_ids_list: list = []) -> None:
        """
        - This function creates Candidate Exam Answer transactions for unattempted questions with score set to 0
        """
        if not len(user_backlog_all_question_ids_list):
            user_backlog_all_question_ids_list = get_detailed_candidate_exam_with_country_based_questions(
                candidate_exam_id, fetch_only_question_ids=True
            )  # type:ignore

        candidate_exam_answers_question_ids_list = list(
            CandidateExamAnswer.objects.filter(candidate_exam_id=candidate_exam_id).values_list("exam_backlog_question", flat=True)
        )

        unattempted_question_ids_list = list(
            set(set(user_backlog_all_question_ids_list) - set(candidate_exam_answers_question_ids_list))  # type:ignore
        )

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

    def __candidate_exam_section_and_subsection_scores_instances_creation(
        self, candidate_exam_id: int, user_backlog_all_question_ids_list: list = []
    ) -> None:
        """
        - This function creates Candidate Exam Section Score and Candidate Exam Subsection Score instances
        """
        if not len(user_backlog_all_question_ids_list):
            user_backlog_all_question_ids_list = get_detailed_candidate_exam_with_country_based_questions(
                candidate_exam_id, fetch_only_question_ids=True
            )  # type:ignore

        candidate_exam_questions_with_sections_and_subsections = ExamBacklogQuestion.objects.filter(
            id__in=user_backlog_all_question_ids_list,
            section_backlog__isnull=False,
        )
        candidate_exam_questions_with_subsections = candidate_exam_questions_with_sections_and_subsections.filter(subsection_backlog__isnull=False)

        section_backlog_questions_details_hashmap = self.__section_with_section_details_hashmap_creation(
            candidate_exam_questions_with_sections_and_subsections
        )

        subsection_backlog_questions_details_hashmap = self.__subsection_backlog_questions_details_hashmap_creation(
            section_backlog_questions_details_hashmap,
            candidate_exam_questions_with_subsections,
        )

        # * Creating the section_score instances
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

        # * Creating the subsection_score instances
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

    def __section_with_section_details_hashmap_creation(self, candidate_exam_questions_with_sections_and_subsections) -> dict:
        """
        - This function creates a hashmap of section with section details
        """
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
        return section_backlog_questions_details_hashmap

    def __subsection_backlog_questions_details_hashmap_creation(
        self, section_backlog_questions_details_hashmap, candidate_exam_questions_with_subsections
    ) -> dict:
        """
        - This function creates a hashmap of subsection with subsection details
        """
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
        return subsection_backlog_questions_details_hashmap

    def __set_response_data_for_attempt_candidate_exam_when_key_not_present(self, request_data: dict, response_data: dict) -> dict:
        """
        - This function sets the response data for attempt candidate exam when key is not present in request data
        """
        candidate_exam_id = request_data.get("candidate_exam_id")
        if not candidate_exam_id:
            ResponseMiddleware.return_now(make_error_response(message="Candidate Exam ID is required"))

        candidate_exam_instance = CandidateExam.objects.filter(id=candidate_exam_id).first()
        if not candidate_exam_instance:
            ResponseMiddleware.return_now(make_error_response(message="Candidate Exam not found"))

        if candidate_exam_instance.exam_status != "assigned":  # type:ignore
            ResponseMiddleware.return_now(make_error_response(message="Exam has already been attempted"))

        candidate_exam_instance = get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id, set_attempted=True)
        self.candidate_exam_data = CandidateExamDetailSerializer(
            candidate_exam_instance, context={"get_retry_hints": candidate_exam_instance.is_preparatory}  # type: ignore
        ).data

        all_questions = self.__get_candidate_exam_all_questions()
        encryption_data = json.dumps({"all_questions": all_questions, "candidate_exam": self.candidate_exam_data})
        key = get_encryption_key()
        encrypted_data = encrypt_message(encryption_data, key)
        response_data["question"] = all_questions[0] if len(all_questions) else {}
        response_data["candidate_exam"] = self.candidate_exam_data
        response_data["key"] = encrypted_data
        return response_data

    def __get_candidate_exam_all_questions(self) -> list:
        """
        - This function gets all the questions from the candidate exam data
        """
        all_questions = self.candidate_exam_data["exam_backlog"].pop("questions")  # type:ignore
        sections = self.candidate_exam_data["exam_backlog"].pop("sections")  # type:ignore
        if len(sections):
            for one_section in sections:
                all_questions.extend(one_section["questions"])
                subsections = one_section["subsections"]
                if len(subsections):
                    for one_subsection in subsections:
                        all_questions.extend(one_subsection["questions"])
        return all_questions

    def __set_response_data_for_attempt_candidate_exam_when_key_present(self, request_data: dict, response_data: dict) -> dict:
        """
        - This function sets the response data for attempt candidate exam when key is present in request data it response with the next question in the exam sequence
        """
        encrypted_data = request_data.get("key")
        decrypted_data = json.loads(decrypt_message(encrypted_data, get_encryption_key()))  # type:ignore
        previous_question_backlog_id = request_data.get("question_backlog_id")
        all_questions = decrypted_data["all_questions"]
        if not previous_question_backlog_id:
            answered_questions_list = list(
                CandidateExamAnswer.objects.filter(candidate_exam_id=decrypted_data["candidate_exam"]["id"], is_attempted=True)
                .values_list("exam_backlog_question", flat=True)
                .distinct()
            )
            previous_question_backlog_id = answered_questions_list[-1] if len(answered_questions_list) else None

        if previous_question_backlog_id:
            previous_question_index = None
            for index, one_question in enumerate(all_questions):
                if str(one_question["id"]) == str(previous_question_backlog_id):
                    previous_question_index = index
                    break
            if previous_question_index == None:
                ResponseMiddleware.return_now(make_error_response(message="Invalid Question ID"))
            next_question_index = previous_question_index + 1  # type:ignore
            if next_question_index >= len(all_questions):
                ResponseMiddleware.return_now(Response(status=status.HTTP_204_NO_CONTENT))
            response_data["question"] = all_questions[next_question_index]
        else:
            response_data["question"] = all_questions[0]
        response_data["candidate_exam"] = decrypted_data["candidate_exam"]
        response_data["key"] = encrypted_data
        return response_data
