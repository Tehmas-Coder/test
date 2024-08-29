from apps.lookups.models import Package
from core.serializers import BaseModelSerializer, get_base_model_fields


class PackageSerializer(BaseModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "abbreviation",
            "users",
            "questions",
            "exams",
            "prep_exams",
            "exam_attempts",
        ] + get_base_model_fields()
