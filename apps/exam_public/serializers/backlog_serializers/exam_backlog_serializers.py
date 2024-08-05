from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklog
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_serializer import (
    ExamBacklogQuestionSerializer,
)
from apps.exam_public.serializers.backlog_serializers.section_backlog_serializer import (
    SectionBacklogSerializer,
)
from apps.exam_public.serializers.backlog_serializers.subsection_backlog_serializer import (
    SubSectionBacklogSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogEditSerializer(BaseModelSerializer):

    class Meta:
        model = ExamBacklog
        fields = [
            "id",
            "exam",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "education_level_name",
            "total_marks",
            "pass_marks",
            "is_global",
        ] + get_base_model_fields()


class ExamBacklogDetailSerializer(BaseModelSerializer):
    sections = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()

    class Meta:
        model = ExamBacklog
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level_name",
            "total_marks",
            "pass_marks",
            "is_global",
            "questions",
            "sections",
        ] + get_base_model_fields()

    def get_sections(self, obj):
        exam_sections = obj.section_backlogs.all()
        return SectionBacklogSerializer(exam_sections, many=True).data

    def get_questions(self, obj):
        exam_questions = obj.backlog_questions.all()
        response_exam_questions = []

        for exam_question in exam_questions:
            # * If the question is not associated with a section
            if not exam_question.section_backlog:
                response_exam_questions.append(ExamBacklogQuestionSerializer(exam_question).data)

        return response_exam_questions

    def get_sections(self, obj):
        section_questions = {}
        subsection_questions = {}
        subsection_objects = {}

        exam_sections = []

        exam_questions = obj.backlog_questions.all()

        for exam_question in exam_questions:
            # * Handling sections
            if exam_question.section_backlog:
                if exam_question.section_backlog.id not in section_questions:
                    section_questions[exam_question.section_backlog.id] = {
                        "section": SectionBacklogSerializer(exam_question.section_backlog).data,
                        "questions": [],
                        "subsections": [],
                    }

                # * Handling section questions
                if exam_question.section_backlog.id and not exam_question.subsection_backlog:
                    section_questions[exam_question.section_backlog.id]["questions"].append(ExamBacklogQuestionSerializer(exam_question).data)

                # * Handling subsections
                if exam_question.subsection_backlog:
                    if exam_question.subsection_backlog.id not in section_questions[exam_question.section_backlog.id]["subsections"]:
                        section_questions[exam_question.section_backlog.id]["subsections"].append(exam_question.subsection_backlog.id)

                        subsection_questions[exam_question.subsection_backlog.id] = []

                        subsection_objects[exam_question.subsection_backlog.id] = SubSectionBacklogSerializer(exam_question.subsection_backlog).data
                    # * Handling subsection questions
                    if exam_question.section_backlog.id and exam_question.subsection_backlog.id:
                        subsection_questions[exam_question.subsection_backlog.id].append(ExamBacklogQuestionSerializer(exam_question).data)

        for section_data in section_questions.values():
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
