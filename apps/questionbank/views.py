import json
from rest_framework import viewsets
from apps.questionbank.models import (
    EducationLevel,
    Question,
    QuestionSubject,
    Subject,
    SubjectEducationLevel,
)
from apps.questionbank.serializers.question_serializers import (
    QuestionDetailSerializer,
    QuestionEditSerializer,
)
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelDetailSerializer,
)
from apps.questionbank.serializers.subject_serializers import SubjectDetailSerializer
from apps.questionbank.serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.db.models import Prefetch
from apps.questionbank.utils.question_utils import get_question_detail_queryset
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from utils.rna_utils import color_print, debug_print


class EducationLevelViewSet(viewsets.ModelViewSet):
    queryset = EducationLevel.objects.all()
    serializer_class = EducationLevelSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectDetailSerializer


class SubjectEducationLevelViewSet(viewsets.ModelViewSet):
    queryset = SubjectEducationLevel.objects.all()
    serializer_class = SubjectEducationLevelDetailSerializer


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = get_question_detail_queryset()
    serializer_class = QuestionDetailSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer(self, *args, **kwargs):
        if self.action in ["create", "partial_update"]:
            return QuestionEditSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        serializer = QuestionDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        serializer = QuestionDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        Question.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
