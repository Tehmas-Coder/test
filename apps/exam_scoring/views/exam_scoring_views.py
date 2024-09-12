from django.db.models import F, Q, Sum
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamAnswer,
    CandidateExamRetryhint,
)
from utils.rna_utils import debug_print, make_error_response


class CandidateExamScoringViewset(viewsets.ViewSet):

    # -------------------------- Candidate Exam Marking -------------------------- #

    def candidate_exam_marking(self, request, *args, **kwargs):
        candidate_exam_id = request.data.get("candidate_exam_id", None)
        if candidate_exam_id is None:
            return make_error_response(message="Candidate Exam id is required")

        candidate_exam_retry_hints_queryset = list(
            CandidateExamRetryhint.objects.filter(candidate_exam_id=candidate_exam_id)
            .annotate(question_total_marks=F("exam_backlog_question__total_marks"))
            .values()
        )
        request_data = request.data.get("questions_scores", None)
        if request_data is None:
            return make_error_response(message="Questions scores are required")

        # * Adding default 0 penalty score to request data scores
        for one_dict in request_data:
            one_dict["penalty_score"] = 0
        # * Fetching all candidate Exam answers from request data ids
        candidate_exam_answers = list(
            CandidateExamAnswer.objects.filter(id__in=[one_dict["candidate_exam_answer"] for one_dict in request_data]).values()
        )

        # * Hashmap for question_id as key and answer_ids as values
        question_answer_ids_hashmap = {}
        for one_dict in request_data:
            answer_id = one_dict["candidate_exam_answer"]
            exam_backlog_question_id = next(
                one_dict["exam_backlog_question_id"] for one_dict in candidate_exam_answers if one_dict["id"] == answer_id
            )
            question_answer_ids_hashmap[exam_backlog_question_id] = answer_id

        # * Loop through all instances of candidate exam retry hints, checks if the question id there matches with the question id of hashmap, then loop through request and matches the answer id, if it is present then it increments the penalty score by the penalty score set by question
        for one_candidate_exam_retry_hint in candidate_exam_retry_hints_queryset:
            question_id = one_candidate_exam_retry_hint["exam_backlog_question_id"]
            if question_id in question_answer_ids_hashmap:
                for one_request_dict in request_data:
                    if one_request_dict["candidate_exam_answer"] == question_answer_ids_hashmap[question_id]:
                        one_request_dict["penalty_score"] = one_request_dict["penalty_score"] + (
                            (one_candidate_exam_retry_hint["penalty_score"] / 100) * one_candidate_exam_retry_hint["question_total_marks"]
                        )

        # * Bulk Update the scores in Answer Table records
        CandidateExamAnswer.objects.bulk_update(
            [
                CandidateExamAnswer(
                    id=one_dict["candidate_exam_answer"],
                    score=one_dict["score"] - one_dict["penalty_score"],
                    is_correct=one_dict["score"] > 0,
                )
                for one_dict in request_data
            ],
            fields=["score", "is_correct"],
        )
        CandidateExam.objects.filter(id=candidate_exam_id).update(exam_status="marked")
        return Response({"message": "Exam questions marked successfully"}, status=status.HTTP_200_OK)

    # -------------------------- Candidate Exam Scoring -------------------------- #

    def candidate_exam_scoring(self, request, *args, **kwargs):
        candidate_exam_id = request.data.get("candidate_exam_id", None)
        if candidate_exam_id is None:
            return make_error_response(message="CandidateExam id is required")

        # * Sum up all the scores
        all_scores_sum = (
            CandidateExamAnswer.objects.filter(
                candidate_exam_id=candidate_exam_id,
            )
            .filter(Q(score__isnull=False))
            .aggregate(total_score=Sum("score"))["total_score"]
        )
        # * Update obtained marks with the sum of scores
        CandidateExam.objects.filter(id=candidate_exam_id).update(obtained_marks=all_scores_sum, exam_status="scored")
        return Response({"message": "Exam scored successfully"}, status=status.HTTP_200_OK)
