from apps.exam_public.models.exam_public_backlog_models import (
    ExamBacklogQuestionCountry,
)
from apps.lookups.serializers.country_serializers import CountrySerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionCountrySerializer(BaseModelSerializer):
    country = CountrySerializer()

    class Meta:
        model = ExamBacklogQuestionCountry
        fields = [
            "id",
            "country",
        ] + get_base_model_fields()
