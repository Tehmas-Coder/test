from django.db.models import Prefetch


def get_question_detailed_queryset(model, tags=False, attempt_responses=False, choices=False, retry_hints=False, subjects=False, all=False):
    from apps.questionbank.models.question_models import QuestionMedia

    question_queryset = (
        model.objects.get_queryset()
        .select_related("type")
        .prefetch_related(
            Prefetch(
                "questionmedia_set",
                QuestionMedia.objects.all().select_related("media"),
            )
        )
    )
    if tags or all:
        question_queryset = question_queryset.prefetch_related("tags")
    if attempt_responses or all:
        question_queryset = question_queryset.prefetch_related("attempt_responses")
    if choices or all:
        from apps.questionbank.models.question_models import (
            QuestionChoice,
            QuestionChoiceMedia,
        )

        question_queryset = question_queryset.prefetch_related(
            Prefetch(
                "choices",
                queryset=QuestionChoice.objects.all().prefetch_related(
                    Prefetch(
                        "questionchoicemedia_set",
                        QuestionChoiceMedia.objects.all().select_related("media"),
                    )
                ),
            )
        )
    if retry_hints or all:
        from apps.questionbank.models.question_models import (
            QuestionRetryHint,
            QuestionRetryHintMedia,
        )

        question_queryset = question_queryset.prefetch_related(
            Prefetch(
                "retry_hints",
                queryset=QuestionRetryHint.objects.all().prefetch_related(
                    Prefetch(
                        "questionretryhintmedia_set",
                        QuestionRetryHintMedia.objects.all().select_related("media"),
                    )
                ),
            )
        )
    if subjects or all:
        from apps.questionbank.models.question_models import QuestionSubject

        question_queryset = question_queryset.prefetch_related(
            Prefetch(
                "subjects",
                queryset=QuestionSubject.objects.select_related(
                    "subject_education_level",
                    "difficulty_level",
                    "measuring_unit",
                    "subject_education_level__subject",
                    "subject_education_level__education_level",
                ).prefetch_related("countries"),
            )
        )
    return question_queryset
