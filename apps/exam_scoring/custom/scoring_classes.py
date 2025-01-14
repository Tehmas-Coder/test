from django.db.models import F, Prefetch, QuerySet, Sum
from rest_framework import status

from apps.exam_public.helpers.candidate_exam_helpers import (
    get_detailed_candidate_exam_with_country_based_questions,
)
from apps.exam_public.helpers.exam_status_webhook import (
    send_exam_status_to_student_apply_webhook,
)
from apps.exam_public.models.exam_public_backlog_models import ExamBacklogQuestion
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
            .select_related("exam_backlog_question_choice", "exam_backlog_question")
            .annotate(penalty_score=Sum("exam_backlog_question__question_fetched_retry_hints__penalty_score"))
        )
        self.__bulk_update_answers_scores(request_data, candidate_exam_answer_queryset)
        length_of_scored_candidate_exam_answers = candidate_exam_answer_queryset.filter(score__isnull=False).count()
        exam_general_questions_scores_sum = (
            candidate_exam_answer_queryset.filter(score__isnull=False, exam_backlog_question__section_backlog__isnull=True).aggregate(
                total_score=Sum("score")
            )["total_score"]
            or 0
        )

        # * Evaluating the score for sections and subsections
        sections_and_subsections_candidate_exam_answers = candidate_exam_answer_queryset.filter(
            exam_backlog_question__section_backlog__isnull=False, score__isnull=False
        ).annotate(
            section_backlog_id=F("exam_backlog_question__section_backlog"), subsection_backlog_id=F("exam_backlog_question__subsection_backlog")
        )
        subsections_candidate_exam_answers = sections_and_subsections_candidate_exam_answers.filter(subsection_backlog_id__isnull=False)
        section_scores_hashmap = self.__get_section_scores_hashmap(sections_and_subsections_candidate_exam_answers)
        subsection_scores_hashmap = self.__get_subsection_scores_hashmap(subsections_candidate_exam_answers, section_scores_hashmap)
        all_sections_score = self.__bulk_update_candidate_exam_section_and_subsection_scores_instances(
            section_scores_hashmap, subsection_scores_hashmap
        )
        all_scores_sum = exam_general_questions_scores_sum + all_sections_score
        candidate_exam_instance_queryset = CandidateExam.objects.filter(id=self.candidate_exam_id).select_related(
            "exam_backlog", "candidate", "candidate__user", "candidate__organization"
        )
        exam_status = "scored" if (len(candidate_exam_answer_queryset) == length_of_scored_candidate_exam_answers) else "marked"
        candidate_exam_instance_queryset.update(obtained_marks=all_scores_sum, exam_status=exam_status)
        candidate_exam_instance = candidate_exam_instance_queryset.first()
        message = "Exam questions marked and scored successfully"
        response_status = status.HTTP_200_OK
        if candidate_exam_instance.candidate.organization and candidate_exam_instance.candidate.organization.token:  # type: ignore
            webhook_result = (
                send_exam_status_to_student_apply_webhook(candidate_exam_instance)
                if exam_status == "marked"
                else send_exam_result_to_student_apply_webhook(candidate_exam_instance)
            )
            if not webhook_result:
                message += ", failed to send webhook request"
                response_status = status.HTTP_307_TEMPORARY_REDIRECT
        if exam_status == "scored":
            candidate_exam_instance.set_exam_result()  # type: ignore
            # * Sending Email notification to the candidate to view exam result
            exam_scoring = ExamScoringNinja(candidate_exam_instance=candidate_exam_instance)
            if not exam_scoring.send_result_email_to_candidate():
                message += ", failed to send email notification"
                response_status = status.HTTP_307_TEMPORARY_REDIRECT

        return {"message": message, "status": response_status}

    def get_candidate_exam_scoresheet(self):
        user_backlog_question_ids_list = get_detailed_candidate_exam_with_country_based_questions(
            self.candidate_exam_id, fetch_only_question_ids=True, setting_score=True
        )
        candidate_exam_backlog_question_instance = (
            CandidateExam.objects.filter(id=self.candidate_exam_id)
            .select_related("exam_backlog")
            .prefetch_related(
                Prefetch(
                    "exam_backlog__backlog_questions",
                    queryset=ExamBacklogQuestion.objects.filter(id__in=user_backlog_question_ids_list)
                    .select_related("section_backlog", "subsection_backlog")
                    .prefetch_related(
                        Prefetch(
                            "section_backlog__section_scores",
                            queryset=CandidateExamSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id),
                        ),
                        Prefetch(
                            "subsection_backlog__subsection_scores",
                            queryset=CandidateExamSubSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id),
                        ),
                        Prefetch("question_answers", queryset=CandidateExamAnswer.objects.all()),
                    )
                    .annotate(obtained_score=Sum("question_answers__score")),
                )
            )
            .first()
        )

        return CandidateExamScoresheetSerializer(candidate_exam_backlog_question_instance).data

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __bulk_update_answers_scores(self, request_data: list, exam_answers_queryset: QuerySet) -> None:
        """
        Bulk Update the scores in Answer Table records with the scores from the request data and also update the is_correct field based on the score
        Sets score after the penalty is deducted
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

    def __get_section_scores_hashmap(self, sections_and_subsections_candidate_exam_answers: QuerySet) -> dict:
        """
        Get the section scores hashmap from the sections and subsections candidate exam answers queryset
        """
        section_scores_hashmap = {}
        for one_answer in sections_and_subsections_candidate_exam_answers:
            section_backlog_id = one_answer.section_backlog_id  # type:ignore
            if section_backlog_id not in section_scores_hashmap:
                section_scores_hashmap[section_backlog_id] = 0
            if one_answer.subsection_backlog_id is None:  # type:ignore
                section_scores_hashmap[section_backlog_id] = section_scores_hashmap[section_backlog_id] + one_answer.score
        return section_scores_hashmap

    def __get_subsection_scores_hashmap(self, subsections_candidate_exam_answers: QuerySet, section_scores_hashmap: dict) -> dict:
        """
        Get the subsection scores hashmap from the subsections candidate exam answers queryset
        """
        subsection_scores_hashmap = {}
        for one_answer in subsections_candidate_exam_answers:
            section_backlog_id = one_answer.section_backlog_id  # type:ignore
            subsection_backlog_id = one_answer.subsection_backlog_id  # type:ignore
            if subsection_backlog_id not in subsection_scores_hashmap:
                subsection_scores_hashmap[subsection_backlog_id] = 0
            subsection_scores_hashmap[subsection_backlog_id] = subsection_scores_hashmap[subsection_backlog_id] + one_answer.score
            section_scores_hashmap[section_backlog_id] = section_scores_hashmap[section_backlog_id] + one_answer.score
        return subsection_scores_hashmap

    def __bulk_update_candidate_exam_section_and_subsection_scores_instances(
        self, section_scores_hashmap: dict, subsection_scores_hashmap: dict
    ) -> int:
        """
        Bulk Update the section and subsection scores instances with the scores from the section_scores_hashmap and subsection_scores_hashmap
        """
        candidate_exam_section_score_queryset = CandidateExamSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id)
        candidate_exam_subsection_score_queryset = CandidateExamSubSectionScore.objects.filter(candidate_exam_id=self.candidate_exam_id)
        self.__bulk_update_section_or_subsection_scores(
            candidate_exam_section_score_queryset, CandidateExamSectionScore, section_scores_hashmap, "section_backlog_id"
        )
        self.__bulk_update_section_or_subsection_scores(
            candidate_exam_subsection_score_queryset, CandidateExamSubSectionScore, subsection_scores_hashmap, "subsection_backlog_id"
        )
        all_sections_score = candidate_exam_section_score_queryset.aggregate(total_score=Sum("score"))["total_score"] or 0
        return all_sections_score

    def __bulk_update_section_or_subsection_scores(self, queryset: QuerySet, model, scores_hashmap: dict, filter_fieldname: str) -> None:
        """
        Bulk Update the scores instances with the scores from the scores_hashmap
        """
        model.objects.bulk_update(
            [
                model(
                    id=queryset.filter(**{filter_fieldname: key}).first().id,  # type: ignore
                    score=value,
                )
                for key, value in scores_hashmap.items()
            ],
            fields=["score"],
        )
