from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionTag


class QuestionTagSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionTag
        fields = ["id", "question", "tag"] + get_base_model_fields()
