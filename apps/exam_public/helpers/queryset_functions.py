from django.db.models import Prefetch, Q, QuerySet


def get_candidate_detailed_queryset(model, organization=False, user=False) -> QuerySet:
    candidate_queryset = model.objects.get_queryset()
    if organization:
        candidate_queryset = candidate_queryset.select_related("organization", "organization__country")
    if user:
        from apps.user.models.user_models import BaseUser

        candidate_queryset = candidate_queryset.prefetch_related(
            Prefetch("user", queryset=BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True))
        )
    return candidate_queryset


def get_candidate_exam_detailed_queryset(
    model,
    exam_backlog: bool = False,
    schedule: bool = False,
    candidate: bool = False,
    q_filter: Q = Q(),
    exam_backlog_question: bool = False,
    get_answers: bool = False,
    exam_backlog_question_filter=Q(),
) -> QuerySet:
    from apps.exam_public.models.exam_public_models import Candidate

    candidate_exam_queryset = model.objects.filter(q_filter)
    if exam_backlog:
        candidate_exam_queryset = candidate_exam_queryset.select_related("exam_backlog")
        if exam_backlog_question:
            from apps.exam_public.models.exam_public_backlog_models import (
                ExamBacklogQuestion,
            )

            candidate_exam_queryset = candidate_exam_queryset.prefetch_related(
                Prefetch(
                    "exam_backlog__backlog_questions",
                    queryset=ExamBacklogQuestion.get_detail_queryset(all=True, get_answers=get_answers, q_filter=exam_backlog_question_filter),
                )
            )
    if schedule:
        candidate_exam_queryset = candidate_exam_queryset.select_related("schedule")
    if candidate:
        candidate_exam_queryset = candidate_exam_queryset.prefetch_related(
            Prefetch("candidate", queryset=Candidate.get_detail_queryset(organization=True, user=True))
        )
    return candidate_exam_queryset


def get_exambacklogquestion_detailed_queryset(model, all=False, get_answers=False, q_filter=Q()) -> QuerySet:
    from apps.exam_public.models.exam_public_backlog_models import (
        ExamBacklogQuestionChoice,
        ExamBacklogQuestionChoiceMedia,
        ExamBacklogQuestionCountry,
        ExamBacklogQuestionMedia,
        ExamBacklogQuestionRetryHint,
        ExamBacklogQuestionRetryHintMedia,
    )

    exam_backlog_question_queryset = model.objects.filter(q_filter)

    if all:
        exam_backlog_question_queryset = exam_backlog_question_queryset.select_related(
            "type",
            "measuring_unit",
            "difficulty_level",
            "section_backlog",
            "section_backlog__measuring_unit",
            "subsection_backlog",
            "subsection_backlog__measuring_unit",
        ).prefetch_related(
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
        )

    if get_answers:
        from apps.exam_public.models.exam_public_models import CandidateExamAnswer

        exam_backlog_question_queryset = exam_backlog_question_queryset.prefetch_related(
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
            )
        )

    return exam_backlog_question_queryset
