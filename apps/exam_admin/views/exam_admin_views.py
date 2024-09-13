from django.db.models import F, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_admin.models.exam_admin_models import (
    Exam,
    ExamSubject,
    ExamSubjectQuestion,
    Schedule,
    Section,
    SubSection,
)
from apps.exam_admin.serializers.exam_serializers import (
    ExamDetailSerializer,
    ExamEditSerializer,
)
from apps.exam_admin.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionBulkCreateSerializer,
    ExamSubjectQuestionBulkUpdateSerializer,
    ExamSubjectQuestionEditSerializer,
    ExamSubjectQuestionSerializer,
)
from apps.exam_admin.serializers.exam_subject_serializers import (
    ExamSubjectDetailSerializer,
    ExamSubjectSerializer,
)
from apps.exam_admin.serializers.schedule_serializers import ScheduleSerializer
from apps.exam_admin.serializers.section_serializers import (
    SectionEditSerializer,
    SectionSerializer,
)
from apps.exam_admin.serializers.subsection_serializers import (
    SubSectionEditSerializer,
    SubSectionSerializer,
)
from apps.exam_admin.utils.exam_utils import create_random_exam
from apps.organization.models.organization_models import (
    Organization,
    OrganizationExam,
    OrganizationPackage,
    OrganizationUser,
)
from utils.rna_utils import (
    make_error_response,
    make_success_response,
    remove_extra_underscore_from_key_names,
)

# ---------------------------------------------------------------------------- #
#                                 EXAM LOOKUPS                                 #
# ---------------------------------------------------------------------------- #


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all().select_related("measuring_unit")
    serializer_class = SectionEditSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SectionSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()
        response = SectionSerializer(section).data
        return Response(response, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()
        response = SectionSerializer(section).data
        return Response(response)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None


class SubSectionViewSet(viewsets.ModelViewSet):
    queryset = SubSection.objects.all().select_related("section", "measuring_unit")
    serializer_class = SubSectionEditSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return SubSectionSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        subsection = serializer.save()
        response = SubSectionSerializer(subsection).data
        return Response(response, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        subsection = serializer.save()
        response = SubSectionSerializer(subsection).data
        return Response(response)


# ---------------------------------------------------------------------------- #
#                                     EXAM                                     #
# ---------------------------------------------------------------------------- #


class ExamViewSet(viewsets.ModelViewSet):
    queryset = Exam.get_detail_queryset()
    serializer_class = ExamEditSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ExamDetailSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        # * Checking Package limit to create Exam for an Organization if the requested user is not superuser
        if not request.user.is_superuser:
            request.data["is_public"] = 0
            organization_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization", flat=True).first()
            if not organization_id:
                return make_error_response(message=f"Failed: User doesn't belong to any organization")
            organization = Organization.objects.get(id=organization_id)
            # * Checking the usage of exams of Organization package
            organization_package = OrganizationPackage.objects.filter(organization=organization).annotate(total_exams=F("package__exams")).last()
            if not (organization_package.exams <= organization_package.total_exams):  # type:ignore
                return make_error_response(message=f"Failed: Your limit to create exams is reached")
        else:
            request.data["is_public"] = 1
        serializer = ExamEditSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        # * Assigning Exam to Organization if the requested user is not superuser
        if not request.user.is_superuser:
            organization_package.exams = organization_package.exams + 1  # type:ignore
            organization_package.save()  # type:ignore
            organization.exams.add(exam.id)  # type:ignore
        response = ExamDetailSerializer(exam).data
        return Response(response, status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            organization_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization", flat=True).first()
            organization_exam_ids = list(OrganizationExam.objects.filter(organization_id=organization_id).values_list("exam", flat=True))
            self.queryset = self.queryset.filter(Q(id__in=organization_exam_ids) | Q(is_public=True))
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        res = super().retrieve(request, *args, **kwargs)
        if not request.user.is_superuser:
            exam_id = res.data["id"]  # type:ignore
            organization_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization", flat=True).first()
            organization_exam = OrganizationExam.objects.filter(organization_id=organization_id, exam_id=exam_id)
            if not ((res.data["is_public"]) or len(organization_exam)):  # type:ignore
                return make_error_response(message=f"Failed: This Exam doesn't belong to your organization")
        return res

    def partial_update(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            exam_id = self.kwargs["pk"]
            organization_id = OrganizationUser.objects.filter(user_id=request.user.id).values_list("organization", flat=True).first()
            organization_exam = OrganizationExam.objects.filter(organization_id=organization_id, exam_id=exam_id)
            if not len(organization_exam):
                return make_error_response(message=f"Failed: This Exam doesn't belong to your organization")
        instance = self.get_object()
        serializer = ExamEditSerializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        exam.refresh_from_db()  # type:ignore
        response = ExamDetailSerializer(exam).data
        return Response(response)

    @action(detail=False, methods=["post"], url_path="create-random")
    def create_random_exam(self, request):
        exam_data = request.data.get("exam_data", {})
        subject_question_count = request.data.get("subject_question_count", None)
        subject_count = request.data.get("subject_count", 0)
        education_level_id = exam_data.get("education_level", None)

        exam = create_random_exam(
            exam_data=exam_data,
            subject_question_count=subject_question_count,
            subject_count=subject_count,
            education_level_id=education_level_id,
        )
        return make_success_response(exam)

    @action(detail=False, methods=["get"], url_path="get-exams-lookup")
    def get_exams_lookup(self, request):
        exam_list_with_detail = remove_extra_underscore_from_key_names(
            list(Exam.objects.all().annotate(education_level_name=F("education_level__name")).values())
        )
        return make_success_response(data=exam_list_with_detail)


# --------------------------------- SUBJECTS --------------------------------- #


class ExamSubjectViewSet(viewsets.ModelViewSet):
    queryset = ExamSubject.objects.all().select_related(
        "exam", "subject_education_level", "subject_education_level__subject", "subject_education_level__education_level"
    )
    serializer_class = ExamSubjectSerializer
    http_method_names = ["post", "delete"]
    pagination_class = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam_subject = serializer.save()
        response = ExamSubjectDetailSerializer(exam_subject).data
        return Response(response, status=status.HTTP_201_CREATED)


# ----------------------------- SUBJECT QUESTIONS ---------------------------- #


class ExamSubjectQuestionViewSet(viewsets.ModelViewSet):
    queryset = ExamSubjectQuestion.objects.all().select_related("exam_subject", "question", "section", "subsection")
    serializer_class = ExamSubjectQuestionSerializer
    http_method_names = ["post", "patch", "delete"]
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "partial_update":
            return ExamSubjectQuestionEditSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam_subject_question = serializer.save()
        response = ExamSubjectQuestionSerializer(exam_subject_question).data
        return Response(response, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exam_subject_question = serializer.save()
        response = ExamSubjectQuestionSerializer(exam_subject_question).data
        return Response(response)

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
