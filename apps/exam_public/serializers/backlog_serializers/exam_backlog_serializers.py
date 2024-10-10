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
from utils.rna_utils import debug_print


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

    def get_questions(self, obj):
        exam_questions = obj.backlog_questions.all()
        response_exam_questions = []

        for exam_question in exam_questions:
            if not exam_question.section_backlog:
                response_exam_questions.append(exam_question)

        return ExamBacklogQuestionSerializer(response_exam_questions, many=True, context=self.context).data

    def get_sections(self, obj):
        section_questions = {}
        subsection_questions = {}
        subsection_objects = {}

        exam_sections = []
        exam_questions = obj.backlog_questions.all()

        for exam_question in exam_questions:
            if exam_question.section_backlog:
                if exam_question.section_backlog.id not in section_questions:
                    section_questions[exam_question.section_backlog.id] = {
                        "section": SectionBacklogSerializer(exam_question.section_backlog).data,
                        "questions": [],
                        "subsections": [],
                    }

                if exam_question.section_backlog.id and not exam_question.subsection_backlog:
                    section_questions[exam_question.section_backlog.id]["questions"].append(
                        ExamBacklogQuestionSerializer(exam_question, context=self.context).data
                    )

                if exam_question.subsection_backlog:
                    if exam_question.subsection_backlog.id not in section_questions[exam_question.section_backlog.id]["subsections"]:
                        section_questions[exam_question.section_backlog.id]["subsections"].append(exam_question.subsection_backlog.id)
                        subsection_questions[exam_question.subsection_backlog.id] = []
                        subsection_objects[exam_question.subsection_backlog.id] = SubSectionBacklogSerializer(exam_question.subsection_backlog).data

                    if exam_question.section_backlog.id and exam_question.subsection_backlog.id:
                        subsection_questions[exam_question.subsection_backlog.id].append(
                            ExamBacklogQuestionSerializer(exam_question, context=self.context).data
                        )

        for section_data in section_questions.values():
            section_questions_total_marks = sum(one_question["total_marks"] for one_question in section_data["questions"])
            subsections_list = []
            for subsection_id in section_data["subsections"]:
                one_subsection_dict = {
                    "subsection": subsection_objects[subsection_id],
                    "questions": subsection_questions[subsection_id],
                }
                one_subsection_dict["subsection"]["total_marks"] = sum(
                    one_question["total_marks"] for one_question in one_subsection_dict["questions"]
                )
                subsections_list.append(one_subsection_dict)
            section_subsections_total_marks = sum(one_subsection["subsection"]["total_marks"] for one_subsection in subsections_list)
            section_data["section"]["total_marks"] = section_questions_total_marks + section_subsections_total_marks
            section_data["subsections"] = subsections_list
            exam_sections.append(section_data)

        return exam_sections


class ExamBacklogQuestionScoresheetSerializer(BaseModelSerializer):
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

    def get_questions(self, obj):
        exam_questions = obj.backlog_questions.all()
        response_exam_questions = []

        for exam_question in exam_questions:
            if not exam_question.section_backlog:
                response_exam_questions.append(
                    {
                        "id": exam_question.id,
                        "total_marks": exam_question.total_marks,
                        "obtained_marks": exam_question.obtained_score,
                    },
                )

        return response_exam_questions

    def get_sections(self, obj):
        section_questions = {}
        subsection_questions = {}
        subsection_objects = {}

        exam_sections = []
        exam_questions = obj.backlog_questions.all()

        for exam_question in exam_questions:
            if exam_question.section_backlog:
                section_score_instance = exam_question.section_backlog.section_scores.all()[0]
                if exam_question.section_backlog.id not in section_questions:
                    section_questions[exam_question.section_backlog.id] = {
                        "section": {
                            "id": exam_question.section_backlog.id,
                            "name": exam_question.section_backlog.title,
                            "total_marks": section_score_instance.total_obtainable_marks,
                            "obtained_marks": section_score_instance.score,
                            "question_count": section_score_instance.question_count,
                            "subsection_count": section_score_instance.subsection_count,
                        },
                        "questions": [],
                        "subsections": [],
                    }

                if exam_question.section_backlog.id and not exam_question.subsection_backlog:
                    section_questions[exam_question.section_backlog.id]["questions"].append(
                        {
                            "id": exam_question.id,
                            "total_marks": exam_question.total_marks,
                            "obtained_marks": exam_question.obtained_score,
                        }
                    )

                if exam_question.subsection_backlog:
                    subsection_score_instance = exam_question.subsection_backlog.subsection_scores.all()[0]
                    if exam_question.subsection_backlog.id not in section_questions[exam_question.section_backlog.id]["subsections"]:
                        section_questions[exam_question.section_backlog.id]["subsections"].append(exam_question.subsection_backlog.id)
                        subsection_questions[exam_question.subsection_backlog.id] = []
                        subsection_objects[exam_question.subsection_backlog.id] = {
                            "id": exam_question.subsection_backlog.id,
                            "name": exam_question.subsection_backlog.title,
                            "total_marks": subsection_score_instance.total_obtainable_marks,
                            "obtained_marks": subsection_score_instance.score,
                            "question_count": subsection_score_instance.question_count,
                        }

                    if exam_question.section_backlog.id and exam_question.subsection_backlog.id:
                        subsection_questions[exam_question.subsection_backlog.id].append(
                            {
                                "id": exam_question.id,
                                "total_marks": exam_question.total_marks,
                                "obtained_marks": exam_question.obtained_score,
                            }
                        )

        for section_data in section_questions.values():
            subsections_list = []
            for subsection_id in section_data["subsections"]:
                one_subsection_dict = {
                    "subsection": subsection_objects[subsection_id],
                    "questions": subsection_questions[subsection_id],
                }
                subsections_list.append(one_subsection_dict)
            section_data["subsections"] = subsections_list
            exam_sections.append(section_data)

        return exam_sections
