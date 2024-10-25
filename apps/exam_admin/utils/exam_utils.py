from typing import Any, Dict, List, Union

from rest_framework.utils.serializer_helpers import ReturnList

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_serializers import (
    ExamDetailSerializer,
    ExamEditSerializer,
)
from apps.exam_admin.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionSerializer,
)
from apps.questionbank.models import Question, Subject
from core.middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response, object_contains_all_values


def create_exam_instance(exam_data):
    exam = ExamEditSerializer(data=exam_data)
    exam.is_valid(raise_exception=True)
    return exam.save()


def create_random_exam(
    exam_data: Dict[str, Any],
    subject_question_count: Dict[str, int],
    subject_count: int,
    education_level_id: int,
) -> Union[ReturnList, Any]:
    """
    This function generates a random exam with a given number of questions from a given question bank.
    """

    def validate_inputs() -> None:
        if not subject_question_count:
            ResponseMiddleware.return_now(make_error_response(message="Question count is required!"))
        if not subject_count:
            ResponseMiddleware.return_now(make_error_response(message="Subject count is required!"))
        if not education_level_id:
            ResponseMiddleware.return_now(make_error_response(message="Education level is required!"))
        return None

    def select_subjects() -> None:
        if not exam_data.get("subjects"):
            # * If subjects are not provided, select random subjects which have at least one question based on subject count
            subjects = Subject.select_random_subjects(subject_question_count, subject_count, education_level_id)
            if not subjects:
                ResponseMiddleware.return_now(make_error_response(message="Not enough subjects found for the given criteria!"))
            exam_data["subjects"] = subjects
        return None

    def get_subject_id(original_exam_data: Dict[str, Any], subject_id: str) -> Union[None, str]:
        if not original_exam_data.get("subjects"):
            # * Break if array index is out of range
            if int(subject_id) >= len(exam_data["subjects"]):
                return None
            # * We select the subject_id from the list of random subjects one by one
            return exam_data["subjects"][int(subject_id)]
        return subject_id

    def fetch_random_questions() -> Dict[str, List[int]]:
        random_subject_questions = {}
        for subject_id, question_count in subject_question_count.items():
            # * If subjects are not provided, then the subject_id is to be treated as the index of the random_subjects list
            subject_id = get_subject_id(original_exam_data, subject_id)
            if subject_id is None:
                break
            random_subject_questions[subject_id] = Question.select_random_questions(education_level_id, subject_id, question_count)
        return random_subject_questions

    def assign_questions_to_subjects(exam_instance: Any, random_subject_questions: Dict[str, List[int]]) -> None:
        # * Assign Questions to Subjects
        for subject_id, question_ids in random_subject_questions.items():
            for sequence, question_id in enumerate(question_ids, start=1):
                exam_question = ExamSubjectQuestionSerializer(
                    data={
                        "exam_subject": {
                            "subject": subject_id,
                            "exam": exam_instance.id,  # type: ignore
                        },
                        "question": question_id,
                        "sequence": sequence,
                    }
                )
                exam_question.is_valid(raise_exception=True)
                exam_question.save()

    def create_exam_instance(exam_data: Dict[str, Any]) -> Any:
        # * Create Exam
        exam = ExamEditSerializer(data=exam_data)
        exam.is_valid(raise_exception=True)
        return exam.save()

    error_response = validate_inputs()
    if error_response:
        return error_response

    original_exam_data = exam_data.copy()

    error_response = select_subjects()

    random_subject_questions = fetch_random_questions()

    # * Check if enough questions are found for the given criteria
    all_subjects_have_questions = object_contains_all_values(random_subject_questions)
    if not all_subjects_have_questions:
        ResponseMiddleware.return_now(make_error_response(message="Not enough questions found for the given criteria!"))

    exam_instance = create_exam_instance(exam_data=exam_data)

    assign_questions_to_subjects(exam_instance, random_subject_questions)

    exam_qs = Exam.get_detail_queryset(all=True).filter(id=exam_instance.id)  # type: ignore

    return ExamDetailSerializer(exam_qs.first()).data
