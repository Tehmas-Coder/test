from apps.questionbank.models import Question, QuestionSubject
from django.db.models import Prefetch
from django.db.models.query import QuerySet


def get_question_detail_queryset() -> QuerySet[Question]:
    return Question.objects.all().prefetch_related(
        "tags",
        "choices",
        "attempt_responses",
        "retry_hints",
        "medias",
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
