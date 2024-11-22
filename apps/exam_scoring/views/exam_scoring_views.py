from cryptography.fernet import Fernet
from django.db.models import F, Prefetch, Sum
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_public.helpers.exam_status_webhook import (
    send_exam_status_to_student_apply_webhook,
)
from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionCountry,
)
from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamAnswer,
)
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamScoresheetSerializer,
)
from apps.exam_scoring.helpers.exam_scoring_helper import ExamScoringNinja
from apps.exam_scoring.helpers.scoring_webhook import (
    send_exam_result_to_student_apply_webhook,
)
from apps.exam_scoring.models.exam_score_models import (
    CandidateExamSectionScore,
    CandidateExamSubSectionScore,
)
from utils.rna_utils import (
    color_print,
    debug_print,
    get_encryption_key,
    make_error_response,
)


class CandidateExamScoringViewset(viewsets.ViewSet):

    # -------------------------- Candidate Exam Marking -------------------------- #

    def candidate_exam_marking(self, request, *args, **kwargs):
        candidate_exam_id = request.data.get("candidate_exam_id", None)
        if candidate_exam_id is None:
            return make_error_response(message="Candidate Exam id is required")

        request_data = request.data.get("questions_scores", None)
        if request_data is None:
            return make_error_response(message="Questions scores are required")
        candidate_exam_answer_queryset = (
            CandidateExamAnswer.objects.filter(candidate_exam_id=candidate_exam_id)
            .select_related(
                "exam_backlog_question_choice",
                "exam_backlog_question",
            )
            .annotate(penalty_score=Sum("exam_backlog_question__question_fetched_retry_hints__penalty_score"))
        )

        # * Bulk Update the scores in Answer Table records
        CandidateExamAnswer.objects.bulk_update(
            [
                CandidateExamAnswer(
                    id=one_dict["candidate_exam_answer"],
                    score=one_dict["score"]
                    - float(
                        next(
                            (
                                one_candidate_exam_answer.penalty_score  # type: ignore
                                for one_candidate_exam_answer in candidate_exam_answer_queryset
                                if one_candidate_exam_answer.id == one_dict["candidate_exam_answer"]  # type: ignore
                                and one_candidate_exam_answer.penalty_score is not None  # type: ignore
                            ),
                            0,
                        )
                    ),
                    is_correct=one_dict["score"] > 0,
                )
                for one_dict in request_data
            ],
            fields=["score", "is_correct"],
        )

        # ---------------------------------- SCORING --------------------------------- #

        # * Sum up scores of questions without sections and subsections in exam
        #  Length of all the scored candidate exam answers
        length_of_scored_candidate_exam_answers = len(candidate_exam_answer_queryset.filter(score__isnull=False))
        # * Answer Queryset of only question directly present in exam
        scored_candidate_exam_answer_queryset = candidate_exam_answer_queryset.filter(
            score__isnull=False, exam_backlog_question__section_backlog__isnull=True
        ).aggregate(total_score=Sum("score"))
        exam_questions_scores_sum = scored_candidate_exam_answer_queryset["total_score"]
        if exam_questions_scores_sum is None:
            exam_questions_scores_sum = 0

        # * Evaluating the score for sections and subsections
        sections_and_subsections_candidate_exam_answers = candidate_exam_answer_queryset.filter(
            exam_backlog_question__section_backlog__isnull=False, score__isnull=False
        ).annotate(
            section_backlog_id=F("exam_backlog_question__section_backlog"),
            subsection_backlog_id=F("exam_backlog_question__subsection_backlog"),
        )
        subsections_candidate_exam_answers = sections_and_subsections_candidate_exam_answers.filter(subsection_backlog_id__isnull=False)

        section_scores_hashmap = {}
        for one_answer in sections_and_subsections_candidate_exam_answers:
            section_backlog_id = one_answer.section_backlog_id  # type:ignore
            if section_backlog_id not in section_scores_hashmap:
                section_scores_hashmap[section_backlog_id] = 0
            if one_answer.subsection_backlog_id is None:  # type:ignore
                section_scores_hashmap[section_backlog_id] = section_scores_hashmap[section_backlog_id] + one_answer.score

        subsection_scores_hashmap = {}
        for one_answer in subsections_candidate_exam_answers:
            section_backlog_id = one_answer.section_backlog_id  # type:ignore
            subsection_backlog_id = one_answer.subsection_backlog_id  # type:ignore
            if subsection_backlog_id not in subsection_scores_hashmap:
                subsection_scores_hashmap[subsection_backlog_id] = 0
            subsection_scores_hashmap[subsection_backlog_id] = subsection_scores_hashmap[subsection_backlog_id] + one_answer.score
            section_scores_hashmap[section_backlog_id] = section_scores_hashmap[section_backlog_id] + one_answer.score

        candidate_exam_section_score_queryset = CandidateExamSectionScore.objects.filter(candidate_exam_id=candidate_exam_id)
        candidate_exam_subsection_score_queryset = CandidateExamSubSectionScore.objects.filter(candidate_exam_id=candidate_exam_id)

        # * Updating the section scores
        CandidateExamSectionScore.objects.bulk_update(
            [
                CandidateExamSectionScore(
                    id=candidate_exam_section_score_queryset.filter(section_backlog_id=one_section).first().id,  # type: ignore
                    score=score,
                )
                for one_section, score in section_scores_hashmap.items()
            ],
            fields=["score"],
        )

        # * Updating the subsection scores
        CandidateExamSubSectionScore.objects.bulk_update(
            [
                CandidateExamSubSectionScore(
                    id=candidate_exam_subsection_score_queryset.filter(subsection_backlog_id=one_subsection).first().id,  # type: ignore
                    score=score,
                )
                for one_subsection, score in subsection_scores_hashmap.items()
            ],
            fields=["score"],
        )

        all_sections_score = candidate_exam_section_score_queryset.aggregate(total_score=Sum("score"))["total_score"]

        if all_sections_score is None:
            all_sections_score = 0
        # * Sum up all the scores for overall exam obtained marks
        all_scores_sum = exam_questions_scores_sum + all_sections_score

        # * Update obtained marks with the sum of scores and exam_status = scored if none of the questions left to mark otherwise set the status to marked
        candidate_exam_instance_queryset = CandidateExam.objects.filter(id=candidate_exam_id).select_related(
            "exam_backlog", "candidate", "candidate__user", "candidate__organization"
        )
        if len(candidate_exam_answer_queryset) == length_of_scored_candidate_exam_answers:
            candidate_exam_instance_queryset.update(obtained_marks=all_scores_sum, exam_status="scored")
            candidate_exam_instance = candidate_exam_instance_queryset.first()
            message = "Exam's all questions are marked and scored successfully"
            response_status = status.HTTP_200_OK
            if candidate_exam_instance.candidate.organization.token:  # type: ignore
                if not send_exam_result_to_student_apply_webhook(candidate_exam_instance):
                    message += ", failed to send webhook request"
                    response_status = status.HTTP_307_TEMPORARY_REDIRECT
            # * Sending Email notification to the candidate to view exam result
            exam_scoring = ExamScoringNinja(candidate_exam_instance=candidate_exam_instance)
            if not exam_scoring.send_result_email_to_candidate():
                message += ", failed to send email notification"
                response_status = status.HTTP_307_TEMPORARY_REDIRECT
        else:
            message = "Exam questions marked and scored successfully"
            response_status = status.HTTP_200_OK
            candidate_exam_instance_queryset.update(obtained_marks=all_scores_sum, exam_status="marked")
            candidate_exam_instance = candidate_exam_instance_queryset.first()
            if not send_exam_status_to_student_apply_webhook(candidate_exam_instance):
                message = message + " but failed to send exam status through webhook"
                response_status = status.HTTP_307_TEMPORARY_REDIRECT
        return Response({"message": message}, status=response_status)

    # * -------------------------- Candidate Exam Scoresheet -------------------------- #

    def candidate_exam_scoresheet(self, request, *args, **kwargs):
        candidate_exam_id = self.kwargs.get("id", None)

        try:
            candidate_exam_id = int(candidate_exam_id)
        except:
            try:
                token = candidate_exam_id[len("token=") :]
                key = get_encryption_key()
                cipher = Fernet(key)
                candidate_exam_id = cipher.decrypt(token).decode()
            except:
                return make_error_response(message="Invalid token")

        candidate_exam_data = (
            CandidateExam.objects.filter(id=candidate_exam_id)
            .annotate(country_id=F("candidate__user__country_id"))
            .values(
                "country_id",
                "exam_backlog",
                "exam_status",
            )
            .first()
        )

        if not candidate_exam_data:
            return make_error_response(message="The requested candidate exam is not present")

        if candidate_exam_data["exam_status"] != "scored":
            return make_error_response(message="The requested candidate exam is not scored yet")

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

        candidate_exam_backlog_question_instance = (
            CandidateExam.objects.filter(id=candidate_exam_id)
            .select_related("exam_backlog")
            .prefetch_related(
                Prefetch(
                    "exam_backlog__backlog_questions",
                    queryset=ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list)
                    .select_related(
                        "section_backlog",
                        "subsection_backlog",
                    )
                    .prefetch_related(
                        Prefetch(
                            "section_backlog__section_scores",
                            queryset=CandidateExamSectionScore.objects.filter(candidate_exam_id=candidate_exam_id),
                        ),
                        Prefetch(
                            "subsection_backlog__subsection_scores",
                            queryset=CandidateExamSubSectionScore.objects.filter(candidate_exam_id=candidate_exam_id),
                        ),
                        Prefetch(
                            "question_answers",
                            queryset=CandidateExamAnswer.objects.all(),
                        ),
                    )
                    .annotate(obtained_score=Sum("question_answers__score")),
                ),
            )
            .first()
        )

        data = CandidateExamScoresheetSerializer(candidate_exam_backlog_question_instance).data
        return Response(data, status=status.HTTP_200_OK)
