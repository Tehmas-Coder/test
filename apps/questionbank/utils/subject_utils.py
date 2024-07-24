from django.db.models import Count, F, Q

from apps.questionbank.models import Subject


def select_random_subjects(
    subject_question_count: dict[str, int], subject_count: int, education_level_id: int
) -> list[int]:
    """
    Select random subjects which have atleast one question based on subject count and question count.

    Args:
        subject_question_count (dict[str, int]): A dictionary of subject_id and question_count.
        subject_count (int): Number of subjects to be selected.
        education_level_id (int): Education level id.

    Returns:
        List[int]: List of random subject ids.

    """
    return list(
        Subject.get_random(
            count=subject_count,
            q_filter=Q(
                Q(education_level_id=education_level_id)
                & Q(question_count__gt=max(subject_question_count.values()))
            ),
            annotation={
                "question_count": Count("subjecteducationlevel__questions"),
                "education_level_id": F("subjecteducationlevel__education_level"),
            },
        ).values_list("id", flat=True)
    )
