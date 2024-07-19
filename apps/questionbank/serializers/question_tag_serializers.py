from core.serializers import BaseModelSerializer
from apps.questionbank.models import QuestionTag


class QuestionTagSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionTag
        fields = ["id", "question", "tag"]
