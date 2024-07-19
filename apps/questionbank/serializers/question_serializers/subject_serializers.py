from apps.questionbank.models import Subject
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class SubjectDetailSerializer(BaseModelSerializer):
    education_levels = EducationLevelSerializer(many=True)

    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "education_levels",
        ] + get_base_model_fields()


class SubjectListSerializer(BaseModelSerializer):
    class Meta:
        model = Subject
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
        ] + get_base_model_fields()
