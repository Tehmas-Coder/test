from apps.exam.models.exam_models import SectionSubSection
from core.serializers import BaseModelSerializer, get_base_model_fields


class SectionSubSectionSerializer(BaseModelSerializer):
    class Meta:
        model = SectionSubSection
        fields = [
            "id",
            "section",
            "subsection",
        ] + get_base_model_fields()
