from rest_framework import serializers

from apps.exam_admin.models.exam_admin_models import ExamSubject
from apps.questionbank.serializers.question_serializers.subject_education_level_serializers import (
    SubjectEducationLevelSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamSubjectDetailSerializer(BaseModelSerializer):
    subject_education_level = SubjectEducationLevelSerializer()

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "subject_education_level",
        ] + get_base_model_fields()

    def to_representation(self, instance):
        from apps.exam_admin.serializers.exam_subject_question_serializer import (
            ExamSubjectQuestionEditSerializer,
        )

        data = super().to_representation(instance)
        data["questions"] = ExamSubjectQuestionEditSerializer(instance.examsubjectquestion_set.all(), many=True).data
        return data


class ExamSubjectListSerializer(serializers.ModelSerializer):
    subject_education_level = SubjectEducationLevelSerializer()

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "subject_education_level",
        ]


class ExamSubjectSerializer(BaseModelSerializer):

    class Meta:
        model = ExamSubject
        fields = [
            "id",
            "exam",
            "subject_education_level",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def create(self, validated_data):
        instance, _ = ExamSubject.objects.get_or_create(
            exam=validated_data["exam"],
            subject_education_level=validated_data["subject_education_level"],
            defaults=validated_data,
        )

        return instance
