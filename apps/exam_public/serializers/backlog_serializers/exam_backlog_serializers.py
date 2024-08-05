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
            "sections",
            "questions",
        ] + get_base_model_fields()

    def get_sections(self, obj):
        exam_sections = obj.section_backlogs.all()
        return SectionBacklogSerializer(exam_sections, many=True).data

    def get_questions(self, obj):
        exam_questions = obj.backlog_questions.all()

        # for exam_subject_question in exam_subject_questions:
        #     # * If the question is not associated with a section
        #     if not exam_subject_question.section:
        #         if exam_subject_question.question:
        #             exam_questions.append(ExamSubjectQuestionDetailSerializer(exam_subject_question).data)

        return ExamBacklogQuestionSerializer(exam_questions, many=True).data
