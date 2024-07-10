from rest_framework import viewsets
from apps.question_bank.models import Question
from apps.question_bank.serializers.question_serializers import QuestionSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    serializer_class = QuestionSerializer
