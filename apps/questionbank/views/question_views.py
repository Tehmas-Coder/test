import json

from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.lookups.custom.lookups_classes import (
    OrganizationResourceQuerysetMutator,
    OrganizationResourceValidator,
)
from apps.questionbank.custom.question_classes import (
    ChoiceMediaExtractor,
    HintMediaExtractor,
    OrganizationPackageQuestionLimitValidator,
    QuestionService,
    QuestionVisibilitySetter,
    RequestMediaParser,
)
from apps.questionbank.filters.question_filters import QuestionFilterBackend
from apps.questionbank.helpers.question_helpers import (
    check_subject_education_level_existence,
)
from apps.questionbank.models.question_models import (
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
from apps.questionbank.serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.education_level_serializers import (
    EducationLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.question_attempt_response_serializers import (
    QuestionAttemptResponseBulkCreateSerializer,
    QuestionAttemptResponseSerializer,
)
from apps.questionbank.serializers.question_serializers.question_choice_media_serializers import (
    QuestionChoiceMediaBulkCreateSerializer,
    QuestionChoiceMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_choice_serializers import (
    QuestionChoiceBulkCreateSerializer,
    QuestionChoiceSerializer,
)
from apps.questionbank.serializers.question_serializers.question_media_serializers import (
    QuestionMediaBulkCreateSerializer,
    QuestionMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_retry_hint_media_serializers import (
    QuestionRetryHintMediaBulkCreateSerializer,
    QuestionRetryHintMediaSerializer,
)
from apps.questionbank.serializers.question_serializers.question_retry_hint_serializers import (
    QuestionRetryHintBulkCreateSerializer,
    QuestionRetryHintSerializer,
)
from apps.questionbank.serializers.question_serializers.question_serializers import (
    QuestionEditSerializer,
    QuestionSerializer,
)
from apps.questionbank.serializers.question_serializers.question_tag_serializers import (
    QuestionTagBulkUpsertSerializer,
    QuestionTagSerializer,
)
from apps.questionbank.serializers.question_serializers.question_type_serializers import (
    QuestionTypeSerializer,
)
from apps.questionbank.serializers.subject_education_level_serializers import (
    SubjectEducationLevelSerializer,
)
from apps.questionbank.serializers.subject_serializers import SubjectSerializer


# ---------------------------------------------------------------------------- #
#                               QUESTION LOOKUPS                               #
# ---------------------------------------------------------------------------- #
class EducationLevelViewSet(viewsets.ModelViewSet):
    queryset = EducationLevel.objects.all().select_related("organization")
    serializer_class = EducationLevelSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        return super().get_queryset()

    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        return super().partial_update(request, *args, **kwargs)


class SubjectViewSet(viewsets.ModelViewSet):
    queryset = Subject.objects.all().select_related("organization")
    serializer_class = SubjectSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        return super().get_queryset()

    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        return super().partial_update(request, *args, **kwargs)


class SubjectEducationLevelViewSet(viewsets.ModelViewSet):
    queryset = SubjectEducationLevel.get_detail_queryset()
    serializer_class = SubjectEducationLevelSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        return super().get_queryset()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        check_subject_education_level_existence(request.data["subject"], request.data["education_level"])
        return super().create(request, *args, **kwargs)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        check_subject_education_level_existence(request.data["subject"], request.data["education_level"], self.get_object().id)
        return super().partial_update(request, *args, **kwargs)


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
    queryset = Question.get_detail_queryset(all=True)
    filter_backends = [QuestionFilterBackend]
    serializer_class = QuestionSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return QuestionEditSerializer
        return super().get_serializer_class()

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset, is_public=True).get_queryset()
        return super().get_queryset()

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_parser = RequestMediaParser()
        request_choice_media_parser = RequestMediaParser(ChoiceMediaExtractor())
        request_hint_media_parser = RequestMediaParser(HintMediaExtractor())
        visibility_setter = QuestionVisibilitySetter()
        organization_validator = OrganizationPackageQuestionLimitValidator()
        question_service = QuestionService(
            request_parser,
            request_choice_media_parser,
            request_hint_media_parser,
            visibility_setter,
            organization_validator,
            self.get_serializer_class(),
        )
        return question_service.create_question(request)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        serializer = self.get_serializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        serializer = QuestionSerializer(self.get_object())
        return Response(serializer.data)

    @action(detail=False, methods=["delete"], url_path="delete-all")
    def delete_all(self, request):
        Question.objects.all().update(meta_status="deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ----------------------------------- MEDIA ---------------------------------- #


class QuestionMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionMedia.objects.all().select_related("media")
    serializer_class = QuestionMediaSerializer
    http_method_names = ["post", "delete"]

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_medias(self, request):
        request_data = RequestMediaParser().parse(request)
        serializer = QuestionMediaBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_medias = serializer.save()
        serializer = QuestionMediaSerializer(question_medias, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete_question_medias(self, request):
        delete_request_ids = request.data.get("ids", [])
        QuestionMedia.objects.filter(id__in=delete_request_ids).update(meta_status="deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ----------------------------------- TAGS ----------------------------------- #


class QuestionTagViewSet(viewsets.ModelViewSet):
    queryset = QuestionTag.objects.all()
    serializer_class = QuestionTagSerializer
    http_method_names = ["post", "delete"]

    @action(detail=False, methods=["post"], url_path="bulk-upsert")
    def bulk_upsert_question_tags(self, request):
        serializer = QuestionTagBulkUpsertSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        question_tags = serializer.save()
        serializer = QuestionTagSerializer(question_tags, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------- CHOICES --------------------------------- #


class QuestionChoiceViewSet(viewsets.ModelViewSet):
    queryset = QuestionChoice.objects.all().prefetch_related("medias")
    serializer_class = QuestionChoiceSerializer
    http_method_names = ["post", "patch", "delete"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = RequestMediaParser().parse(request)
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_choice = serializer.save()
        serializer = QuestionChoiceSerializer(question_choice, context={"source": True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_choice = serializer.save()
        serializer = QuestionChoiceSerializer(question_choice, context={"source": True})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_choices(self, request):
        request_data = RequestMediaParser().parse(request)
        request_data = RequestMediaParser(ChoiceMediaExtractor()).parse_media(request, request_data)
        serializer = QuestionChoiceBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_choice_medias = serializer.save()
        serializer = QuestionChoiceSerializer(question_choice_medias, many=True, context={"source": True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ------------------------------- CHOICES MEDIA ------------------------------ #


class QuestionChoiceMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionChoiceMedia.objects.all().select_related("media")
    serializer_class = QuestionChoiceMediaSerializer
    http_method_names = ["post", "delete"]

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_choice_medias(self, request):
        request_data = RequestMediaParser().parse(request)
        serializer = QuestionChoiceMediaBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_choice_medias = serializer.save()
        serializer = QuestionChoiceMediaSerializer(question_choice_medias, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete_question_choice_medias(self, request):
        delete_request_ids = request.data.get("ids", [])
        QuestionChoiceMedia.objects.filter(id__in=delete_request_ids).update(meta_status="deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)


# ------------------------- QUESTION ATTEMPT RESPONSE ------------------------ #


class QuestionAttemptResponseViewSet(viewsets.ModelViewSet):
    queryset = QuestionAttemptResponse.objects.all()
    serializer_class = QuestionAttemptResponseSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_attempt_reponse(self, request):
        request_data = request.data
        serializer = QuestionAttemptResponseBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_attempt_reponse = serializer.save()
        serializer = QuestionAttemptResponseSerializer(question_attempt_reponse, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# -------------------------------- RETRY HINTS ------------------------------- #


class QuestionRetryHintViewSet(viewsets.ModelViewSet):
    queryset = QuestionRetryHint.objects.all().prefetch_related("medias")
    serializer_class = QuestionRetryHintSerializer
    http_method_names = ["post", "patch", "delete"]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        request_data = RequestMediaParser().parse(request)
        serializer = self.get_serializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_retry_hint = serializer.save()
        serializer = QuestionRetryHintSerializer(question_retry_hint, context={"source": True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        question_retry_hint = serializer.save()
        serializer = QuestionRetryHintSerializer(question_retry_hint, context={"source": True})
        return Response(serializer.data)

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_retry_hints(self, request):
        request_data = json.loads(request.data["data"])

        # Extract media for retry hints
        for retry_hint in request_data.get("retry_hints", []):
            retry_hint_medias = retry_hint.pop("medias", [])
            if retry_hint_medias:
                retry_hint["medias"] = []
                for key in retry_hint_medias:
                    file = request.FILES.get(key)
                    if file:
                        retry_hint["medias"].append({"file": file})

        serializer = QuestionRetryHintBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_retry_hint_medias = serializer.save()
        serializer = QuestionRetryHintSerializer(question_retry_hint_medias, many=True, context={"source": True})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


# ----------------------------- RETRY HINT MEDIA ----------------------------- #


class QuestionRetryHintMediaViewSet(viewsets.ModelViewSet):
    queryset = QuestionRetryHintMedia.objects.all().select_related("media")
    serializer_class = QuestionRetryHintMediaSerializer
    http_method_names = ["post", "delete"]

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_question_retry_hint_medias(self, request):
        request_data = RequestMediaParser().parse(request)
        serializer = QuestionRetryHintMediaBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        question_retry_hint_medias = serializer.save()
        serializer = QuestionRetryHintMediaSerializer(question_retry_hint_medias, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="bulk-delete")
    def bulk_delete_question_retry_hint_medias(self, request):
        delete_request_ids = request.data.get("ids", [])
        QuestionRetryHintMedia.objects.filter(id__in=delete_request_ids).update(meta_status="deleted")  # Bulk Delete
        return Response(status=status.HTTP_204_NO_CONTENT)
