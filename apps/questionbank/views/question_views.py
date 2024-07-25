import json

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.questionbank.models import (
    DifficultyLevel,
    EducationLevel,
    Question,
    QuestionAttemptResponse,
    QuestionChoice,
    QuestionChoiceMedia,
    QuestionMedia,
    QuestionRetryHint,
    QuestionRetryHintMedia,
    QuestionTag,
    QuestionType,
    Subject,
    SubjectEducationLevel,
)
from apps.questionbank.serializers.question_serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.question_attempt_response_serializers import (
    QuestionAttemptResponseSerializer,
)
from apps.questionbank.serializers.question_serializers.question_choice_media_serializers import (
    QuestionChoiceMediaBulkCreateSerializer,
    QuestionChoiceMediaEditSerializer,
    QuestionChoiceMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_choice_serializers import (
    QuestionChoiceDetailSerializer,
    QuestionChoiceSerializer,
)
from apps.questionbank.serializers.question_serializers.question_media_serializers import (
    QuestionMediaBulkCreateSerializer,
    QuestionMediaDetailSerializer,
    QuestionMediaEditSerializer,
)
from apps.questionbank.serializers.question_serializers.question_retry_hint_media_serializers import (
    QuestionRetryHintMediaEditSerializer,
    QuestionRetryHintMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_retry_hint_serializers import (
    QuestionRetryHintDetailSerializer,
    QuestionRetryHintSerializer,
)
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionDetailSerializer,
    QuestionEditSerializer,
)
from apps.questionbank.serializers.question_serializers.question_tag_serializers import (
    QuestionTagSerializer,
)
from apps.questionbank.serializers.question_serializers.question_type_serializers import (
    QuestionTypeSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_education_level_serializers import (
    SubjectEducationLevelDetailSerializer,
    SubjectEducationLevelEditSerializer,
)
from apps.questionbank.serializers.question_serializers.subject_serializers import (
    SubjectDetailSerializer,
)
from utils.rna_utils import debug_print


# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #
class EducationLevelViewSet(viewsets.ModelViewSet):
    queryset = EducationLevel.objects.all()
    serializer_class = EducationLevelSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all()
    serializer_class = SubjectDetailSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


class SubjectEducationLevelViewSet(viewsets.ModelViewSet):
    queryset = SubjectEducationLevel.objects.all()
    serializer_class = SubjectEducationLevelDetailSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return SubjectEducationLevelEditSerializer
        return super().get_serializer_class()


class DifficultyLevelViewSet(viewsets.ModelViewSet):
    queryset = DifficultyLevel.objects.all()
    serializer_class = DifficultyLevelSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


class QuestionTypeViewSet(viewsets.ModelViewSet):
    queryset = QuestionType.objects.all()
    serializer_class = QuestionTypeSerializer
    http_method_names = ["get"]
    pagination_class = None


# ---------------------------------------------------------------------------- #
#                                   QUESTION                                   #
# ---------------------------------------------------------------------------- #
class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.get_detail_queryset()
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
        for hint in request_data.get("retry_hints", []):
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
        for choice in request_data.get("choices", []):
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

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_medias(self, request):
        request_data = json.loads(request.data["data"])

        # * Extract medias for question
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

        serializer = QuestionMediaBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_medias = serializer.save()
        serializer = QuestionMediaDetailSerializer(question_medias, many=True)
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
        serializer = QuestionChoiceDetailSerializer(question_choice)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_choice = serializer.save()
        serializer = QuestionChoiceDetailSerializer(question_choice)
        return Response(serializer.data)


# ------------------------------- CHOICES MEDIA ------------------------------ #


class QuestionChoiceMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionChoiceMedia.objects.all()
    serializer_class = QuestionChoiceMediaEditSerializer
    http_method_names = ["post", "delete"]

    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        if res.data:
            instance = QuestionChoiceMedia.objects.get(id=res.data["id"])
            serializer = QuestionChoiceMediaSerializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return res

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_choice_medias(self, request):
        request_data = json.loads(request.data["data"])

        # * Extract medias for question choice
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

        serializer = QuestionChoiceMediaBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_choice_medias = serializer.save()
        serializer = QuestionChoiceMediaSerializer(question_choice_medias, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------- QUESTION ATTEMPT RESPONSE ------------------------ #


class QuestionAttemptResponseViewSet(viewsets.ModelViewSet):
    queryset = QuestionAttemptResponse.objects.all()
    serializer_class = QuestionAttemptResponseSerializer
    http_method_names = ["get", "post", "patch", "delete"]


# -------------------------------- RETRY HINTS ------------------------------- #


class QuestionRetryHintViewSet(viewsets.ModelViewSet):
    queryset = QuestionRetryHint.objects.all()
    serializer_class = QuestionRetryHintSerializer
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
        question_retry_hint = serializer.save()
        serializer = QuestionRetryHintDetailSerializer(question_retry_hint)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ----------------------------- RETRY HINT MEDIA ----------------------------- #


class QuestionRetryHintMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionRetryHintMedia.objects.all()
    serializer_class = QuestionRetryHintMediaEditSerializer
    http_method_names = ["post", "delete"]

    def create(self, request, *args, **kwargs):
        res = super().create(request, *args, **kwargs)
        if res.data:
            instance = QuestionRetryHintMedia.objects.get(id=res.data["id"])
            serializer = QuestionRetryHintMediaSerializer(instance)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return res
