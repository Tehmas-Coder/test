from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from apps.exam_admin.models.exam_admin_models import ExamSubject, ExamSubjectQuestion
from apps.exam_admin.serializers.exam_subject_serializers import ExamSubjectSerializer
from apps.questionbank.serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionSerializer,
)
from apps.questionbank.serializers.subject_serializers import SubjectSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamSubjectQuestionDetailSerializer(BaseModelSerializer):
    subject = SubjectSerializer(read_only=True, source="exam_subject.subject_education_level.subject")
    education_level = EducationLevelSerializer(read_only=True, source="exam_subject.subject_education_level.education_level")
    question = serializers.SerializerMethodField()

    class Meta:
        model = ExamSubjectQuestion
        fields = [
            "id",
            "subject",
            "education_level",
            "question",
            "section",
            "subsection",
            "total_marks",
            "sequence",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def get_question(self, obj):
        question_data = QuestionSerializer(obj.question).data
        question_subject_data = question_data.pop("subjects")  # type: ignore
        exam_subject_id = obj.exam_subject.subject_education_level.subject.id
        exam_subject_education_level_id = obj.exam_subject.subject_education_level.education_level.id

        question_more_data: dict = {}
        for one_dict in question_subject_data:
            if (one_dict["subject"]["id"] == exam_subject_id) and (one_dict["education_level"]["id"] == exam_subject_education_level_id):
                question_more_data["difficulty_level"] = one_dict.pop("difficulty_level")
                question_more_data["measuring_unit"] = one_dict.pop("measuring_unit")
                question_more_data["countries"] = one_dict.pop("countries")
                question_more_data["time_limit"] = one_dict.pop("time_limit")
                question_more_data["total_marks"] = one_dict.pop("total_marks")
                question_more_data["is_optional"] = one_dict.pop("is_optional")
                question_more_data["is_global"] = one_dict.pop("is_global")
                break
        question_data.update(question_more_data)  # type:ignore
        return question_data


class ExamSubjectQuestionSerializer(BaseModelSerializer):
    exam_subject = ExamSubjectSerializer()

    class Meta:
        model = ExamSubjectQuestion
        fields = [
            "id",
            "exam_subject",
            "question",
            "section",
            "subsection",
            "total_marks",
            "sequence",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def __init__(self, *args, **kwargs):
        self._context = kwargs.get("context", {})
        if self._context.get("mutator", False):
            self.fields.pop("exam_subject")
            self.fields.pop("question")
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        exam_subject_data = validated_data.pop("exam_subject")
        exam_subject_instance = ExamSubjectSerializer().create(exam_subject_data)
        instance = ExamSubjectQuestion.objects.create(exam_subject=exam_subject_instance, **validated_data)
        return instance


class ExamSubjectQuestionBulkCreateSerializer(serializers.Serializer):
    create_list = ExamSubjectQuestionSerializer(many=True)

    def create(self, validated_data):
        validated_data = validated_data["create_list"]
        exam_subjects = ExamSubject.objects.all()

        for one_dict in validated_data:
            exam_subject_request_data = one_dict.get("exam_subject")

            for one_exam_subject in exam_subjects:
                if (one_exam_subject.exam_id == exam_subject_request_data["exam"].id) and (  # type:ignore
                    one_exam_subject.subject_education_level_id == exam_subject_request_data["subject_education_level"].id  # type:ignore
                ):
                    one_dict["exam_subject"] = one_exam_subject

        exam_subject_question_instances = [ExamSubjectQuestion(**one_exam_subject_question) for one_exam_subject_question in validated_data]

        ExamSubjectQuestion.objects.bulk_create(exam_subject_question_instances)
        created_exam_subject_questions_instances = ExamSubjectQuestion.objects.all().order_by("-created_at")[: len(exam_subject_question_instances)]
        created_exam_subject_questions_instances = sorted(created_exam_subject_questions_instances, key=lambda instance: instance.id)  # type:ignore

        return created_exam_subject_questions_instances


class ExamSubjectQuestionBulkUpdateSerializer(serializers.Serializer):
    update_list = serializers.ListField(child=serializers.DictField(child=serializers.IntegerField()))

    def bulk_update_sequence(self, validated_data):
        validated_data = validated_data["update_list"]
        input_exam_subject_question_ids = [one_dict.get("id") for one_dict in validated_data]
        exam_subject_question_instances = ExamSubjectQuestion.objects.filter(pk__in=input_exam_subject_question_ids)

        if len(input_exam_subject_question_ids) != len(exam_subject_question_instances):
            raise ValidationError({"Exam Subject Question Errors": "Some of the provided exam subject questions doesn't exist"})

        exam_subject_question_id_sequence_hashmap = {}
        for one_dict in validated_data:
            id = one_dict["id"]
            if id not in exam_subject_question_id_sequence_hashmap:
                exam_subject_question_id_sequence_hashmap[id] = one_dict["sequence"]

        for one_instance in exam_subject_question_instances:
            one_instance.sequence = exam_subject_question_id_sequence_hashmap[one_instance.id]  # type: ignore

        ExamSubjectQuestion.objects.bulk_update(exam_subject_question_instances, ["sequence"])

        return exam_subject_question_instances
