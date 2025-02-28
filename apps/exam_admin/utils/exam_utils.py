from dataclasses import dataclass
from typing import Any

from django.db.models import Model, Prefetch, Q, QuerySet

from apps.exam_admin.custom.exam_classes import (
    ExamService,
    ExamVisibilitySetter,
    OrganizationPackageExamLimitValidator,
)
from apps.exam_admin.models.exam_admin_models import ExamSubjectQuestion
from apps.exam_admin.serializers.exam_serializers import ExamSerializer
from apps.lookups.custom.lookups_classes import OrganizationResourceQuerysetMutator
from apps.questionbank.models.question_models import Question, QuestionSubject
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


@dataclass
class RandomExamCreator:
    """
    This class is used to create a random exam based on the provided data.

    :Attributes:
    - `exam_data` (Any): The exam data.
    - `subject_education_levels` (Any): The subject education levels.
    - `difficulty_levels` (Any): The difficulty levels.
    - `question_types` (Any): The question types.
    - `question_count` (Any): The question count.
    - `is_candidate` (Any): The is candidate flag.
    - `organization_id` (Any): The organization id.

    :Methods:
    - `create_random_exam()`: Creates a random exam based on the provided data.
    """

    exam_data: Any
    subject_education_levels: Any
    difficulty_levels: Any
    question_types: Any
    question_count: Any
    is_candidate: Any
    organization_id: Any

    def __post_init__(self):
        self.created_exam_instance = None

    def create_random_exam(self) -> Model:
        try:
            self.__request_values_validator()
        except Exception as e:
            ResponseMiddleware.return_now(make_error_response(message=str(e)))
        self.__create_exam_instance()
        self.__create_exam_subjects_questions()
        return self.created_exam_instance  # type: ignore

    # ---------------------------------------------------------------------------- #
    #                                PRIVATE METHODS                               #
    # ---------------------------------------------------------------------------- #

    def __request_values_validator(self):
        if not self.exam_data:
            raise ValueError("Exam data is required")
        if not self.subject_education_levels:
            raise ValueError("Subject education levels are required")
        if not self.question_count:
            raise ValueError("Question count is required")

    def __create_exam_instance(self):
        self.exam_data["subjects"] = self.subject_education_levels
        if self.is_candidate:
            self.__create_exam_by_candidate()
        else:
            self.__create_exam_by_staff()

    def __create_exam_by_staff(self):
        visibility_setter = ExamVisibilitySetter()
        organization_validator = OrganizationPackageExamLimitValidator()
        exam_service = ExamService(
            exam_data=self.exam_data,
            visibility_setter=visibility_setter,
            organization_validator=organization_validator,
            serializer_class=ExamSerializer,
        )
        self.created_exam_instance = exam_service.create_exam()

    def __create_exam_by_candidate(self):
        exam_serializer = ExamSerializer(data=self.exam_data, context={"mutator": True})
        exam_serializer.is_valid(raise_exception=True)
        self.created_exam_instance = exam_serializer.save()

    def __create_exam_subjects_questions(self):
        exam_marks = 0
        questions = self.__get_questions()
        exam_subjects = list(self.created_exam_instance.subjects.through.objects.filter(exam_id=self.created_exam_instance.pk))  # type: ignore
        exam_subject_questions = []
        question_sequence = 0
        for question in questions:
            question_sequence = question_sequence + 1
            question_subject = list(question.subjects.all())[0]  # type:ignore
            for exam_subject in exam_subjects:
                if exam_subject.subject_education_level == question_subject.subject_education_level:
                    exam_subject_questions.append(
                        ExamSubjectQuestion(
                            exam_subject_id=exam_subject.pk,
                            question_id=question.pk,
                            total_marks=question_subject.total_marks,
                            sequence=question_sequence,
                        )
                    )
                    exam_marks = exam_marks + question_subject.total_marks
                    break
        ExamSubjectQuestion.objects.bulk_create(exam_subject_questions)
        self.created_exam_instance.total_marks = exam_marks  # type:ignore
        self.created_exam_instance.save()  # type:ignore

    def __get_questions(self) -> QuerySet:
        q_filter = Q(
            subjects__subject_education_level__in=self.subject_education_levels,
        )
        if self.difficulty_levels:
            q_filter &= Q(subjects__difficulty_level__in=self.difficulty_levels)
        if self.question_types:
            q_filter &= Q(type__in=self.question_types)
        if self.is_candidate:
            q_filter &= Q(organization_id=self.organization_id) | Q(organization_id=None)
        question_queryset = (
            Question.objects.filter(q_filter)
            .prefetch_related(Prefetch("subjects", queryset=QuestionSubject.objects.select_related("subject_education_level")))
            .distinct()
            .order_by("?")
        )
        questions = OrganizationResourceQuerysetMutator(queryset=question_queryset, is_public=True).get_queryset()[: self.question_count]
        return questions
