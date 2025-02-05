from django.db import transaction
from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.custom.exam_classes import (
    ExamService,
    ExamVisibilitySetter,
    OrganizationPackageExamLimitValidator,
)
from apps.exam_admin.filters.exam_filters import ExamFilterBackend
from apps.exam_admin.models.exam_admin_models import (
    Exam,
    ExamSubject,
    ExamSubjectQuestion,
    Schedule,
    Section,
    SubSection,
)
from apps.exam_admin.serializers.exam_serializers import ExamSerializer
from apps.exam_admin.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionBulkCreateSerializer,
    ExamSubjectQuestionBulkUpdateSerializer,
    ExamSubjectQuestionSerializer,
)
from apps.exam_admin.serializers.exam_subject_serializers import ExamSubjectSerializer
from apps.exam_admin.serializers.schedule_serializers import ScheduleSerializer
from apps.exam_admin.serializers.section_serializers import SectionSerializer
from apps.exam_admin.serializers.subsection_serializers import SubSectionSerializer
from apps.exam_admin.utils.exam_utils import RandomExamCreator
from apps.lookups.custom.lookups_classes import (
    OrganizationResourceQuerysetMutator,
    OrganizationResourceValidator,
)
from utils.rna_utils import (
    debug_print,
    make_success_response,
    remove_extra_underscore_from_key_names,
)

# ---------------------------------------------------------------------------- #
#                                 EXAM LOOKUPS                                 #
# ---------------------------------------------------------------------------- #


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all().order_by("-id")
    serializer_class = ScheduleSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        return super().get_queryset()

    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        return super().partial_update(request, *args, **kwargs)


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().select_related("measuring_unit")
    serializer_class = SectionSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


class SubSectionViewSet(viewsets.ModelViewSet):
    queryset = SubSection.objects.all().select_related("measuring_unit")
    serializer_class = SubSectionSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


# ---------------------------------------------------------------------------- #
#                                     EXAM                                     #
# ---------------------------------------------------------------------------- #


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.get_detail_queryset(all=True)
    serializer_class = ExamSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [ExamFilterBackend]
    EXAM_NOT_AVAILABLE_MESSAGE = f"Failed: This Exam doesn't belong to your organization"

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset, is_public=True).get_queryset().order_by("-id")
        return super().get_queryset()

    def get_serializer_context(self):
        if self.action in ["retrieve", "list"]:
            return {"selector": True}
        if self.action in ["create", "partial_update"]:
            return {"mutator": True}

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        visibility_setter = ExamVisibilitySetter()
        organization_validator = OrganizationPackageExamLimitValidator()
        exam_service = ExamService(
            exam_data=request.data,
            visibility_setter=visibility_setter,
            organization_validator=organization_validator,
            serializer_class=self.serializer_class,
        )
        exam_instance = exam_service.create_exam()
        response_data = ExamSerializer(self.queryset.get(pk=exam_instance.pk), context={"selector": True}).data
        return Response(response_data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        OrganizationResourceValidator(instance_organization_id=instance.organization_id).validate()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response = ExamSerializer(self.get_object(), context={"selector": True}).data
        return Response(response)

    @transaction.atomic
    @action(detail=False, methods=["post"], url_path="create-random")
    def create_random_exam(self, request):
        request_data = request.data
        create_random_exam_instance = RandomExamCreator(
            exam_data=request_data.get("exam_data"),
            subject_education_levels=request_data.get("subject_education_levels"),
            difficulty_levels=request_data.get("difficulty_levels"),
            question_types=request_data.get("question_types"),
            question_count=request_data.get("question_count"),
            is_candidate=None,
            organization_id=None,
        )
        exam_instance = create_random_exam_instance.create_random_exam()
        response_data = ExamSerializer(self.queryset.get(pk=exam_instance.pk), context={"selector": True}).data
        return Response(response_data)

    @action(detail=False, methods=["get"], url_path="get-exams-lookup")
    def get_exams_lookup(self, request):
        exam_queryset = Exam.objects.filter(exam_status="active").annotate(education_level_name=F("education_level__name")).values().order_by("-id")
        exam_list_with_detail = remove_extra_underscore_from_key_names(
            list(OrganizationResourceQuerysetMutator(queryset=exam_queryset, is_public=True).get_queryset())
        )
        return make_success_response(data=exam_list_with_detail)


# --------------------------------- SUBJECTS --------------------------------- #


class ExamSubjectViewSet(viewsets.ModelViewSet):
    queryset = (
        ExamSubject.objects.all()
        .prefetch_related("examsubjectquestion_set")
        .select_related("exam", "subject_education_level", "subject_education_level__subject", "subject_education_level__education_level")
    )
    serializer_class = ExamSubjectSerializer
    http_method_names = ["post", "delete"]
    pagination_class = None

    def get_serializer_context(self):
        return {"selector": True, "include_questions": True}


# ----------------------------- SUBJECT QUESTIONS ---------------------------- #


class ExamSubjectQuestionViewSet(viewsets.ModelViewSet):
    queryset = ExamSubjectQuestion.objects.all().select_related("exam_subject", "question", "section", "subsection")
    serializer_class = ExamSubjectQuestionSerializer
    http_method_names = ["post", "patch", "delete"]
    pagination_class = None

    def get_serializer_context(self):
        if self.action == "partial_update":
            return {"mutator": True}
        return super().get_serializer_context()

    @action(detail=False, methods=["post"], url_path="bulk-create")
    def bulk_create_exam_subject_question(self, request):
        request_data = {"create_list": request.data}
        serializer = ExamSubjectQuestionBulkCreateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        exam_subject_questions = serializer.save()
        serializer = ExamSubjectQuestionSerializer(exam_subject_questions, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["patch"], url_path="bulk-update")
    def bulk_update_exam_subject_question_sequence(self, request):
        request_data = {"update_list": request.data}
        serializer = ExamSubjectQuestionBulkUpdateSerializer(data=request_data)
        serializer.is_valid(raise_exception=True)
        exam_subject_questions = serializer.bulk_update_sequence(serializer.validated_data)  # type:ignore
        serializer = ExamSubjectQuestionSerializer(exam_subject_questions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
