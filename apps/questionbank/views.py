from rest_framework import viewsets
from apps.questionbank.models import Question
from apps.questionbank.serializers.question_serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
