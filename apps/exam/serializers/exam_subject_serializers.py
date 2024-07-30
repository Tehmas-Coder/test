from apps.exam.models.exam_models import ExamSubject
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectListSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
import django.db.models.base
from rest_framework import serializers
from utils.rna_utils import color_print, debug_print


class ExamSubjectDetailSerializer(BaseModelSerializer):
    subject = SubjectListSerializer()

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "subject",
        ] + get_base_model_fields()

    def to_representation(self, instance):
        from apps.exam.serializers.exam_subject_question_serializer import (
            ExamSubjectQuestionEditSerializer,
        )

        data = super().to_representation(instance)
        data["questions"] = ExamSubjectQuestionEditSerializer(instance.examsubjectquestion_set.all(), many=True).data
        return data


class ExamSubjectListSerializer(serializers.ModelSerializer):
    subject = SubjectListSerializer()

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "subject",
        ]


class ExamSubjectSerializer(BaseModelSerializer):

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "exam",
            "subject",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def create(self, validated_data):
        instance, _ = ExamSubject.objects.get_or_create(
            exam=validated_data["exam"],
            subject=validated_data["subject"],
            defaults=validated_data,
        )

        return instance
