from apps.questionbank.models import SubjectEducationLevel
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubjectEducationLevelSerializer(BaseModelSerializer):
    class Meta:
        model = SubjectEducationLevel
        fields = [
            "id",
            "subject",
            "education_level",
            "organization",
        ] + get_base_model_fields()

        read_only_fields = ["id"]

    def create(self, validated_data):
        instance, _ = self.Meta.model.objects.get_or_create(
            subject=validated_data["subject"],
            education_level=validated_data["education_level"],
            defaults=validated_data,
        )
        return instance

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if not self.context.get("mutator"):
            representation["subject"] = SubjectSerializer(instance.subject).data
            representation["education_level"] = EducationLevelSerializer(instance.education_level).data
        return representation
