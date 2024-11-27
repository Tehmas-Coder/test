from apps.questionbank.models.question_models import DifficultyLevel
from core.serializers import BaseModelSerializer


class DifficultyLevelSerializer(BaseModelSerializer):
    class Meta:
        model = DifficultyLevel
        fields = [
            "id",
            "name",
            "slug",
            "code",
            "abbreviation",
            "sequence",
        ] + BaseModelSerializer.Meta.fields
        read_only_fields = ["id", "slug"]
