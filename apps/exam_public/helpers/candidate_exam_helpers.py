from django.db.models import F, Prefetch, Sum

from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestion,
    ExamBacklogQuestionChoice,
    ExamBacklogQuestionChoiceMedia,
    ExamBacklogQuestionCountry,
    ExamBacklogQuestionMedia,
    ExamBacklogQuestionRetryHint,
    ExamBacklogQuestionRetryHintMedia,
)
from apps.exam_public.models.exam_public_models import CandidateExam
from apps.exam_public.serializers.candidate_exam_serializers import (
    CandidateExamDetailSerializer,
)
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


def get_detailed_candidate_exam_with_country_based_questions(candidate_exam_id, queryset, set_attempted=False):
    """
    Get detailed candidate exam with country based questions
    :param candidate_exam_id: Candidate exam id, queryset: Queryset
    :return: Detailed candidate exam with country based questions
    """
    candidate_exam_data = (
        CandidateExam.objects.filter(id=candidate_exam_id)
        .annotate(country_id=F("candidate__user__country_id"))
        .values(
            "country_id",
            "exam_backlog",
            "total_obtainable_marks",
        )
        .first()
    )

    if not candidate_exam_data:
        ResponseMiddleware.return_now(make_error_response(message="The requested candidate exam data is not present"))

    exam_question_backlog = list(ExamBacklogQuestion.objects.filter(exam_backlog_id=candidate_exam_data["exam_backlog"]).values("is_global", "id"))  # type: ignore
    is_global_exam_question_backlog_ids_list = [one_dict["id"] for one_dict in exam_question_backlog if one_dict["is_global"]]

    exam_question_backlog_ids = [one_dict["id"] for one_dict in exam_question_backlog if not one_dict["is_global"]]
    is_not_global_exam_question_backlog_ids_list: list = list(
        ExamBacklogQuestionCountry.objects.filter(
            exam_backlog_question_id__in=exam_question_backlog_ids,
            country_id=candidate_exam_data["country_id"],  # type: ignore
        ).values_list("exam_backlog_question", flat=True)
    )
    final_user_backlog_question_ids_list = is_global_exam_question_backlog_ids_list + is_not_global_exam_question_backlog_ids_list

    if not candidate_exam_data["total_obtainable_marks"]:  # type: ignore
        question_instances_total_marks = ExamBacklogQuestion.objects.filter(id__in=final_user_backlog_question_ids_list).aggregate(
            total_score=Sum("total_marks")
        )["total_score"]
        CandidateExam.objects.filter(id=candidate_exam_id).update(
            total_obtainable_marks=question_instances_total_marks if question_instances_total_marks != None else 0
        )

    if set_attempted:
        CandidateExam.objects.filter(id=candidate_exam_id).update(exam_status="attempted")

    candidate_exam_backlog_question_instance = queryset.filter(id=candidate_exam_id).prefetch_related(
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
                        Prefetch("exambacklogquestionchoicemedia_set", queryset=ExamBacklogQuestionChoiceMedia.objects.all().select_related("media"))
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

    return CandidateExamDetailSerializer(
        candidate_exam_backlog_question_instance, context={"get_retry_hints": candidate_exam_backlog_question_instance.is_preparatory}
    ).data
