from typing import Any, Dict, List, Union

from django.db.models import Count, F, Prefetch, Q
from django.db.models.query import QuerySet
from rest_framework.response import Response
from rest_framework.utils.serializer_helpers import ReturnList

from apps.exam.models.exam_models import Exam, ExamSubjectQuestion
from apps.exam.serializers.exam_serializers import (
    ExamDetailSerialzer,
    ExamEditSerializer,
)
from apps.exam.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionSerializer,
)
from apps.questionbank.models import Question, Subject
from apps.questionbank.utils.question_utils import get_question_detail_queryset
from utils.rna_utils import debug_print, make_error_response


def get_exam_detail_queryset() -> QuerySet[Exam]:
    return (
        Exam.objects.all()
        .select_related("education_level")
        .prefetch_related(
            "examsubject_set",
            "examsubject_set__subject",
            "examsubject_set__examsubjectquestion_set",
            "examsubject_set__examsubjectquestion_set__section",
            "examsubject_set__examsubjectquestion_set__subsection",
            Prefetch(
                "examsubject_set__examsubjectquestion_set__question",
                queryset=get_question_detail_queryset(),
            ),
        )
    )


def create_random_exam(
    exam_data: dict,
    subject_question_count: dict[str, int],
    subject_count: int,
    education_level_id: int,
) -> Union[Response, ReturnList | Any]:
    """
    This function generates a random exam with a given number of questions from a given question bank.
    """
    if not subject_question_count:
        return make_error_response(message="Question count is required!")
    if not subject_count:
        return make_error_response(message="Subject count is required!")
    if not education_level_id:
        return make_error_response(message="Education level is required!")

    original_exam_data = exam_data.copy()

    if not exam_data.get("subjects"):
        # * If subjects are not provided, select random subjects which have atleast one question based on subject count
        random_subjects = list(
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

        if not random_subjects:
            return make_error_response(
                message="Not enough subjects found for the given criteria!"
            )

        exam_data["subjects"] = random_subjects

    random_subject_questions = {}
    for subject_id, question_count in subject_question_count.items():
        # * If subjects are not provided, then the subject_id is to be treated as the index of the random_subjects list
        if not original_exam_data.get("subjects"):
            # * break if array index is out of range
            if int(subject_id) >= len(exam_data["subjects"]):
                break

            subject_id = exam_data["subjects"][
                int(subject_id)
            ]  # * we select the subject_id from the list of random subjects one by one

        random_subject_questions[subject_id] = list(
            Question.get_random(
                count=question_count,
                q_filter=Q(
                    Q(subject_education_levels__subject=subject_id)
                    & Q(subject_education_levels__education_level=education_level_id)
                ),
            ).values_list("id", flat=True)
        )

    debug_print(random_subject_questions)

    if not all(random_subject_questions.values()):
        return make_error_response(
            message="Not enough questions found for the given criteria!"
        )

    # * Create Exam
    exam = ExamEditSerializer(data=exam_data)
    exam.is_valid(raise_exception=True)
    exam_instance = exam.save()

    # * Assign Questions to Subjects
    for subject_id, question_ids in random_subject_questions.items():
        question_counter = 1
        for question_id in question_ids:
            exam_question = ExamSubjectQuestionSerializer(
                data={
                    "exam_subject": {
                        "subject": subject_id,
                        "exam": exam_instance.id,  # type: ignore
                    },
                    "question": question_id,
                    "sequence": question_counter,
                }
            )
            exam_question.is_valid(raise_exception=True)
            exam_question.save()
            question_counter += 1

    exam_qs = get_exam_detail_queryset().filter(id=exam_instance.id)  # type: ignore

    return ExamDetailSerialzer(exam_qs.first()).data
