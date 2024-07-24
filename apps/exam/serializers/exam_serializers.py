from rest_framework import serializers

from apps.exam.models.exam_models import Exam, ExamSubjectQuestion
from apps.exam.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionDetailSerializer,
)
from apps.exam.serializers.section_serializers import SectionSerializer
from apps.exam.serializers.subsection_serializers import SubSectionSerializer
from apps.questionbank.models import Subject
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import color_print, debug_print
from apps.exam.serializers.exam_subject_serializers import ExamSubjectListSerializer


class ExamEditSerializer(BaseModelSerializer):
    subjects = serializers.PrimaryKeyRelatedField(
        queryset=Subject.objects.all(), many=True, required=True
    )

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "total_marks",
            "pass_marks",
            "subjects",
            "is_global",
        ] + get_base_model_fields()


class ExamDetailSerialzer(BaseModelSerializer):
    education_level = EducationLevelSerializer()
    questions = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    exam_subjects = serializers.SerializerMethodField()

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "total_marks",
            "pass_marks",
            "is_global",
            "exam_subjects",
            "questions",
            "sections",
        ] + get_base_model_fields()

    def get_exam_subjects(self, obj):
        exam_subjects = obj.examsubject_set.all()
        return ExamSubjectListSerializer(exam_subjects, many=True).data

    def get_questions(self, obj):
        exam_questions = []
        exam_subjects = obj.examsubject_set.all()
        for exam_subject in exam_subjects:
            exam_subject_questions = exam_subject.examsubjectquestion_set.all()
            for exam_subject_question in exam_subject_questions:
                # * If the question is not associated with a section
                if not exam_subject_question.section:
                    try:
                        if exam_subject_question.question:
                            exam_questions.append(
                                ExamSubjectQuestionDetailSerializer(
                                    exam_subject_question
                                ).data
                            )
                    except ExamSubjectQuestion.question.RelatedObjectDoesNotExist:
                        pass
        return exam_questions

    def get_sections(self, obj):
        section_questions = {}
        subsection_questions = {}
        subsection_objects = {}

        exam_sections = []

        exam_subjects = obj.examsubject_set.all()

        for exam_subject in exam_subjects:
            exam_subject_questions = exam_subject.examsubjectquestion_set.all()

            for exam_subject_question in exam_subject_questions:
                # * Handling sections
                if exam_subject_question.section:
                    if exam_subject_question.section.id not in section_questions:
                        section_questions[exam_subject_question.section.id] = {
                            "section": SectionSerializer(
                                exam_subject_question.section
                            ).data,
                            "questions": [],
                            "subsections": [],
                        }

                    # * Handling section questions
                    if (
                        exam_subject_question.section.id
                        and not exam_subject_question.subsection
                    ):
                        section_questions[exam_subject_question.section.id][
                            "questions"
                        ].append(
                            ExamSubjectQuestionDetailSerializer(
                                exam_subject_question
                            ).data
                        )

                    # * Handling subsections
                    if exam_subject_question.subsection:
                        if (
                            exam_subject_question.subsection.id
                            not in section_questions[exam_subject_question.section.id][
                                "subsections"
                            ]
                        ):
                            section_questions[exam_subject_question.section.id][
                                "subsections"
                            ].append(exam_subject_question.subsection.id)

                            subsection_questions[
                                exam_subject_question.subsection.id
                            ] = []

                            subsection_objects[exam_subject_question.subsection.id] = (
                                SubSectionSerializer(
                                    exam_subject_question.subsection
                                ).data
                            )
                        # * Handling subsection questions
                        if (
                            exam_subject_question.section.id
                            and exam_subject_question.subsection.id
                        ):
                            subsection_questions[
                                exam_subject_question.subsection.id
                            ].append(
                                ExamSubjectQuestionDetailSerializer(
                                    exam_subject_question
                                ).data
                            )

        for section_id, section_data in section_questions.items():
            subsections_list = []
            for subsection_id in section_data["subsections"]:
                subsections_list.append(
                    {
                        "subsection": subsection_objects[subsection_id],
                        "questions": subsection_questions[subsection_id],
                    }
                )
            section_data["subsections"] = subsections_list
            exam_sections.append(section_data)

        return exam_sections
