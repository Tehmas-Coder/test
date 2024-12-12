from apps.exam_admin.models.exam_admin_models import ExamSubject
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


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

    def to_representation(self, instance):
        from apps.exam_admin.serializers.exam_subject_question_serializer import (
            ExamSubjectQuestionEditSerializer,
        )

        rep = super().to_representation(instance)
        if self.context.get("selector", False):
            rep["subject_education_level"] = SubjectEducationLevelSerializer(instance.subject_education_level).data
            rep.pop("exam")
        if self.context.get("include_questions", False):
            rep["questions"] = ExamSubjectQuestionEditSerializer(instance.examsubjectquestion_set.all(), many=True).data
        return rep
