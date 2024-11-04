from django.forms import model_to_dict
from rest_framework import serializers

from apps.exam_admin.models.exam_admin_models import Exam
from apps.exam_admin.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionDetailSerializer,
)
from apps.exam_admin.serializers.exam_subject_serializers import (
    ExamSubjectListSerializer,
)
from apps.exam_admin.serializers.section_serializers import SectionSerializer
from apps.exam_admin.serializers.subsection_serializers import (
    SubSectionEditSerializer,
    SubSectionSerializer,
)
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamEditSerializer(BaseModelSerializer):
    subjects = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = Exam
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "organization",
            "total_marks",
            "pass_marks",
            "exam_status",
            "is_public",
            "is_global",
            "subjects",
        ] + get_base_model_fields()

    def create(self, validated_data):
        self.fields.pop("subjects")
        subjects = validated_data.pop("subjects")
        exam = super().create(validated_data)
        exam.subjects.set(subjects)
        return exam


class ExamDetailSerializer(BaseModelSerializer):
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
            "organization",
            "total_marks",
            "pass_marks",
            "exam_status",
            "is_public",
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
                    if exam_subject_question.question:
                        exam_questions.append(ExamSubjectQuestionDetailSerializer(exam_subject_question).data)

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
                            "section": SectionSerializer(exam_subject_question.section).data,
                            "questions": [],
                            "subsections": [],
                        }

                    # * Handling section questions
                    if exam_subject_question.section.id and not exam_subject_question.subsection:
                        section_questions[exam_subject_question.section.id]["questions"].append(
                            ExamSubjectQuestionDetailSerializer(exam_subject_question).data
                        )

                    # * Handling subsections
                    if exam_subject_question.subsection:
                        if exam_subject_question.subsection.id not in section_questions[exam_subject_question.section.id]["subsections"]:
                            section_questions[exam_subject_question.section.id]["subsections"].append(exam_subject_question.subsection.id)

                            subsection_questions[exam_subject_question.subsection.id] = []

                            subsection_objects[exam_subject_question.subsection.id] = SubSectionSerializer(exam_subject_question.subsection).data
                        # * Handling subsection questions
                        if exam_subject_question.section.id and exam_subject_question.subsection.id:
                            subsection_questions[exam_subject_question.subsection.id].append(
                                ExamSubjectQuestionDetailSerializer(exam_subject_question).data
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

        section_instances = [model_to_dict(one_instance) for one_instance in obj.sections.all()]

        # * Handling Sections which are not included yet because of not containing questions

        section_instances_hashmap = {}
        for one_section_instance in section_instances:
            section_id = one_section_instance["id"]
            if section_id not in section_instances_hashmap:
                section_instances_hashmap[section_id] = one_section_instance

        for one_exam_section in exam_sections:
            if one_exam_section["section"]["id"] in section_instances_hashmap:
                section_instances_hashmap.pop(one_exam_section["section"]["id"])

        for one_section_instance in section_instances_hashmap.values():
            section_dict = {
                "section": one_section_instance,
                "questions": [],
                "subsections": [],
            }

            exam_sections.append(section_dict)

        # * Handling Subsections which are not included yet because of not containing questions

        subsections_hashmap = {
            model_to_dict(one_section)["id"]: [model_to_dict(one_subsection) for one_subsection in one_section.subsections.all()]
            for one_section in obj.sections.all()
        }

        # Remove sections with no subsections
        subsections_hashmap = {k: v for k, v in subsections_hashmap.items() if v}

        for one_section in exam_sections:
            one_section_id = one_section["section"]["id"]
            if one_section_id in subsections_hashmap:
                existing_subsections = {one_subsection["subsection"]["id"] for one_subsection in one_section["subsections"]}

                for one_subsection_in_hashmap in subsections_hashmap[one_section_id]:
                    one_subsection_in_hashmap_id = one_subsection_in_hashmap["id"]

                    if one_subsection_in_hashmap_id not in existing_subsections:
                        one_section["subsections"].append(
                            {
                                "subsection": one_subsection_in_hashmap,
                                "questions": [],
                            }
                        )
                        existing_subsections.add(one_subsection_in_hashmap_id)

        return exam_sections


class ExamDetailSerializerForBacklogs(BaseModelSerializer):
    education_level = EducationLevelSerializer()
    exam_subjects = serializers.SerializerMethodField()
    questions = serializers.SerializerMethodField()
    sections = serializers.SerializerMethodField()
    subsections = serializers.SerializerMethodField()

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
            "exam_status",
            "is_public",
            "is_global",
            "exam_subjects",
            "questions",
            "sections",
            "subsections",
        ] + get_base_model_fields()

    def get_exam_subjects(self, obj):
        self.exam_subjects = obj.examsubject_set.all()
        return ExamSubjectListSerializer(self.exam_subjects, many=True).data

    def get_questions(self, obj):
        exam_questions = []
        for exam_subject in self.exam_subjects:  # type:ignore
            exam_subject_questions = exam_subject.examsubjectquestion_set.all()
            if exam_subject_questions:
                exam_questions.extend(ExamSubjectQuestionDetailSerializer(exam_subject_questions, many=True).data)

        return exam_questions

    def get_sections(self, obj):
        self.exam_sections = obj.sections.all()
        return SectionSerializer(self.exam_sections, many=True).data

    def get_subsections(self, obj):
        exam_subsections = []
        for one_section in self.exam_sections:
            one_section_subsections = one_section.subsections.all()
            if one_section_subsections:
                exam_subsections.extend((SubSectionEditSerializer(one_section_subsections, many=True).data))

        return exam_subsections
