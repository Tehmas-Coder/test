from apps.exam.models.exam_models import ExamSubjectQuestion
from apps.exam.serializers.exam_subject_serializers import ExamSubjectSerializer
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionDetailSerializer,
    QuestionSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectListSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamSubjectQuestionEditSerializer(BaseModelSerializer):

    class Meta:
        model = ExamSubjectQuestion
        fields = [
            "id",
            "section",
            "subsection",
            "sequence",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]


class ExamSubjectQuestionDetailSerializer(BaseModelSerializer):
    subject = SubjectListSerializer(read_only=True, source="exam_subject.subject")
    question = QuestionSerializer(read_only=True)

    class Meta:
        model = ExamSubjectQuestion
        fields = [
            "id",
            "subject",
            "question",
            "section",
            "subsection",
            "sequence",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]


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
            "sequence",
        ] + get_base_model_fields()

        read_only_fields = [
            "id",
        ]

    def create(self, validated_data):
        exam_subject_data = validated_data.pop("exam_subject")
        exam_subject_instance = ExamSubjectSerializer().create(exam_subject_data)
        instance = ExamSubjectQuestion.objects.create(
            exam_subject=exam_subject_instance, **validated_data
        )
        return instance
