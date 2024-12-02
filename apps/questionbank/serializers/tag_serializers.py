from apps.questionbank.models.question_models import Tag
from core.serializers import BaseModelSerializer, get_base_model_fields


class TagSerializer(BaseModelSerializer):
    class Meta:
        model = Tag
        fields = [
            "id",
            "name",
            "code",
            "abbreviation",
            "description",
            "organization",
        ] + get_base_model_fields()
