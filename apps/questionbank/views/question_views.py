import json
from rest_framework import viewsets
from apps.questionbank.models import (EducationLevel, Question, QuestionAttemptResponse,
    QuestionChoice, QuestionChoiceMedia, QuestionMedia, QuestionSubject, QuestionTag, Subject,
    SubjectEducationLevel)
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

from utils.rna_utils import debug_print
from apps.questionbank.serializers.question_media_serializers import (
    QuestionMediaDetailSerializer,
    QuestionMediaEditSerializer,
)
from rest_framework.parsers import FormParser, MultiPartParser
from apps.questionbank.serializers.question_tag_serializers import QuestionTagSerializer
from apps.questionbank.serializers.question_choice_serializers import (
    QuestionChoiceSerializer,
)
from apps.questionbank.serializers.question_choice_media_serializers import (
    QuestionChoiceMediaEditSerializer, QuestionChoiceMediaSerializer)
from apps.questionbank.serializers.question_attempt_response_serializers import (
    QuestionAttemptResponseSerializer)


class EducationLevelViewSet(viewsets.ModelViewSet):
    queryset = EducationLevel.objects.all()
    serializer_class = EducationLevelSerializer


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectDetailSerializer


class SubjectEducationLevelViewSet(viewsets.ModelViewSet):
    queryset = SubjectEducationLevel.objects.all()
    serializer_class = SubjectEducationLevelDetailSerializer


# ---------------------------------------------------------------------------- #
#                                   QUESTION                                   #
# ---------------------------------------------------------------------------- #
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = get_question_detail_queryset()
    serializer_class = QuestionDetailSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def parse_media(self, request):
        request_data = json.loads(request.data["data"])

        # Extract media for questions
        media_keys = request_data.pop("medias", [])
        request_data["medias"] = []
        for key in media_keys:
            file = request.FILES.get(key)
            if file:
                request_data["medias"].append(
                    {
                        "file": file,
                    }
                )

        # Extract media for hints
        for hint in request_data["retry_hints"]:
            hint_medias = hint.pop("medias", [])
            if hint["has_media"]:
                hint["medias"] = []
                for key in hint_medias:
                    file = request.FILES.get(key)
                    if file:
                        hint["medias"].append(
                            {
                                "file": file,
                            }
                        )

        # Extract media for choices
        for choice in request_data["choices"]:
            choice_medias = choice.pop("medias", [])
            if choice["has_media"]:
                choice["medias"] = []
                for key in choice_medias:
                    file = request.FILES.get(key)
                    if file:
                        choice["medias"].append(
                            {
                                "file": file,
                            }
                        )

        return request_data

    def get_serializer(self, *args, **kwargs):
        if self.action in ["create", "partial_update"]:
            return QuestionEditSerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)

    def create(self, request, *args, **kwargs):
        if "data" in request.data:
            request_data = self.parse_media(request)
        else:
            request_data = request.data
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        serializer = QuestionDetailSerializer(question)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        request_data = request.data
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request_data, partial=True)
        serializer.is_valid(raise_exception=True)
        question = serializer.save()
        serializer = QuestionDetailSerializer(question)
        return Response(serializer.data)

    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        Question.objects.all().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ----------------------------------- MEDIA ---------------------------------- #


class QuestionMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionMedia.objects.all()
    serializer_class = QuestionMediaEditSerializer
    http_method_names = ["post", "delete"]
    parser_classes = [FormParser, MultiPartParser]

    def create(self, request, *args, **kwargs):
        request_data = request.data
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_media = serializer.save()
        serializer = QuestionMediaDetailSerializer(question_media)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ----------------------------------- TAGS ----------------------------------- #


class QuestionTagViewSet(viewsets.ModelViewSet):
    queryset = QuestionTag.objects.all()
    serializer_class = QuestionTagSerializer
    http_method_names = ["post", "delete"]


# ---------------------------------- CHOICES --------------------------------- #
class QuestionChoiceViewSet(viewsets.ModelViewSet):
    queryset = QuestionChoice.objects.all().prefetch_related("medias")
    serializer_class = QuestionChoiceSerializer
    http_method_names = ["post", "patch", "delete"]

    def create(self, request, *args, **kwargs):
        request_data = request.data.copy()
        if len(request.FILES) > 0:
            request_data["medias"] = []
        for file in request.FILES:
            request_data["medias"].append({"file": request.FILES[file]})
            request_data.pop(file)
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_choice = serializer.save()
        serializer = QuestionChoiceSerializer(question_choice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_choice = serializer.save()
        serializer = QuestionChoiceSerializer(question_choice)
        return Response(serializer.data)

# ------------------------------- CHOICES MEDIA ------------------------------ #

class QuestionChoiceMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionChoiceMedia.objects.all()
    serializer_class = QuestionChoiceMediaEditSerializer
    http_method_names = ['post', 'delete']

    def create(self, request, *args, **kwargs):
        res =  super().create(request, *args, **kwargs)
        if res.data:
            instance = QuestionChoiceMedia.objects.get(id=res.data['id'])
            serializer = QuestionChoiceMediaSerializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return res

# ------------------------- QUESTION ATTEMPT RESPONSE ------------------------ #

class QuestionAttemptResponseViewSet(viewsets.ModelViewSet):
    queryset = QuestionAttemptResponse.objects.all()
    serializer_class = QuestionAttemptResponseSerializer
    http_method_names = ['get', 'post', 'patch', 'delete']

# -------------------------------- RETRY HINTS ------------------------------- #

