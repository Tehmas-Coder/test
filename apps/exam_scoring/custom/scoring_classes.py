from django.db.models import F, QuerySet, Sum
from rest_framework import status

from apps.exam_public.helpers.exam_status_webhook import (
    send_exam_status_to_student_apply_webhook,
)
from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamAnswer,
)
from apps.exam_scoring.helpers.exam_scoring_helper import ExamScoringNinja
from apps.exam_scoring.helpers.scoring_webhook import (
    send_exam_result_to_student_apply_webhook,
)
from apps.exam_scoring.models.exam_scoring_models import (
    CandidateExamSectionScore,
    CandidateExamSubSectionScore,
)


class CandidateExamScoring:

    def __init__(self, candidate_exam_id: int) -> None:
        self.candidate_exam_id = candidate_exam_id

    def mark_candidate_exam(self, request_data: list) -> dict:
        candidate_exam_answer_queryset = (
            CandidateExamAnswer.objects.filter(candidate_exam_id=self.candidate_exam_id)
            .select_related(
                "exam_backlog_question_choice",
                "exam_backlog_question",
            )
            .annotate(penalty_score=Sum("exam_backlog_question__question_fetched_retry_hints__penalty_score"))
        )

        # * Bulk Update the scores in Answer Table records
        self.__bulk_update_answers_scores(request_data, candidate_exam_answer_queryset)

        # ---------------------------------- SCORING --------------------------------- #

        # * Sum up scores of questions without sections and subsections in exam
        #  Length of all the scored candidate exam answers
        length_of_scored_candidate_exam_answers = len(candidate_exam_answer_queryset.filter(score__isnull=False))
        # * Answer Queryset of only question directly present in exam
        exam_general_questions_scores_sum = candidate_exam_answer_queryset.filter(
            score__isnull=False, exam_backlog_question__section_backlog__isnull=True
        ).aggregate(total_score=Sum("score"))["total_score"]
        if exam_general_questions_scores_sum is None:
            exam_general_questions_scores_sum = 0

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

        candidate_exam_section_score_queryset = CandidateExamSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id)
        candidate_exam_subsection_score_queryset = CandidateExamSubSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id)

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
        all_scores_sum = exam_general_questions_scores_sum + all_sections_score

        # * Update obtained marks with the sum of scores and exam_status = scored if none of the questions left to mark otherwise set the status to marked
        candidate_exam_instance_queryset = CandidateExam.objects.filter(id=self.candidate_exam_id).select_related(
            "exam_backlog", "candidate", "candidate__user", "candidate__organization"
        )
        if len(candidate_exam_answer_queryset) == length_of_scored_candidate_exam_answers:
            candidate_exam_instance_queryset.update(obtained_marks=all_scores_sum, exam_status="scored")
            candidate_exam_instance = candidate_exam_instance_queryset.first()
            candidate_exam_instance.set_exam_result()  # type: ignore
            message = "Exam's all questions are marked and scored successfully"
            response_status = status.HTTP_200_OK
            if candidate_exam_instance.candidate.organization and candidate_exam_instance.candidate.organization.token:  # type: ignore
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
            if candidate_exam_instance.candidate.organization and candidate_exam_instance.candidate.organization.token:  # type: ignore
                if not send_exam_status_to_student_apply_webhook(candidate_exam_instance):
                    message = message + " but failed to send exam status through webhook"
                    response_status = status.HTTP_307_TEMPORARY_REDIRECT

        return {"message": message, "status": response_status}

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __bulk_update_answers_scores(self, request_data: list, exam_answers_queryset: QuerySet) -> None:
        """
        Bulk Update the scores in Answer Table records
        """
        CandidateExamAnswer.objects.bulk_update(
            [
                CandidateExamAnswer(
                    id=one_dict["candidate_exam_answer"],
                    score=one_dict["score"]
                    - float(
                        next(
                            (
                                one_candidate_exam_answer.penalty_score  # type: ignore
                                for one_candidate_exam_answer in exam_answers_queryset
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
