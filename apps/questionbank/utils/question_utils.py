from django.db.models import Prefetch
from django.db.models.query import Q, QuerySet

from apps.questionbank.models import Question, QuestionSubject


def get_question_detail_queryset() -> QuerySet[Question]:
    return Question.objects.all().prefetch_related(
        "tags",
        "choices",
        "attempt_responses",
        "retry_hints",
        "questionmedia_set",
        "questionmedia_set__media",
        "type",
        Prefetch(
            "subjects",
            queryset=QuestionSubject.objects.select_related(
                "subject_education_level",
                "difficulty_level",
                "measuring_unit",
                "subject_education_level__subject",
                "subject_education_level__education_level",
            ).prefetch_related("countries"),
        ),
    )


def select_random_questions(
    education_level_id: int, subject_id: int | str, question_count: int
) -> list[int]:
    """
    Select random questions based on the given subject and education level.

    Args:
        education_level_id (int): Education level id.
        subject_id (int | str): Subject id.
        question_count (int): Number of questions to be selected.

    Returns:
        List[int]: List of random question ids.
    """

    return list(
        Question.get_random(
            count=question_count,
            q_filter=Q(
                Q(subject_education_levels__subject=subject_id)
                & Q(subject_education_levels__education_level=education_level_id)
            ),
        ).values_list("id", flat=True)
    )
