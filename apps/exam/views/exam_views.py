from django.db.models import Prefetch
from rest_framework import viewsets
from rest_framework.response import Response

from apps.exam.models.exam_models import (
    Exam,
    ExamSubject,
    ExamSubjectQuestion,
    Section,
    SubSection,
)
from apps.exam.serializers.exam_serializers import (
    ExamDetailSerialzer,
    ExamEditSerializer,
)
from apps.exam.serializers.exam_subject_question_serializer import (
    ExamSubjectQuestionEditSerializer,
    ExamSubjectQuestionSerializer,
)
from apps.exam.serializers.exam_subject_serializers import (
    ExamSubjectDetailSerializer,
    ExamSubjectSerializer,
)
from apps.exam.serializers.section_serializers import (
    SectionEditSerializer,
    SectionSerializer,
)
from apps.exam.serializers.subsection_serializers import (
    SubSectionEditSerializer,
    SubSectionSerializer,
)
from apps.questionbank.utils.question_utils import get_question_detail_queryset

# ---------------------------------------------------------------------------- #
#                                 EXAM LOOKUPS                                 #
# ---------------------------------------------------------------------------- #


class SectionViewSet(viewsets.ModelViewSet):
    queryset = Section.objects.all()
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
        return Response(response)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        section = serializer.save()
        response = SectionSerializer(section).data
        return Response(response)


class SubSectionViewSet(viewsets.ModelViewSet):
    queryset = SubSection.objects.all()
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
        return Response(response)

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
    queryset = (
        Exam.objects.all()
        .select_related("education_level")
        .prefetch_related(
            Prefetch(
                "examsubject_set__examsubjectquestion_set__question",
                queryset=get_question_detail_queryset(),
            ),
            "subjects",
            "examsubject_set",
            "examsubject_set__subject",
            "examsubject_set__examsubjectquestion_set",
            "examsubject_set__examsubjectquestion_set__section",
            "examsubject_set__examsubjectquestion_set__subsection",
        )
    )
    serializer_class = ExamEditSerializer
    http_method_names = ["get", "post", "patch", "delete"]

    def get_serializer_class(self):
        if self.action in ["retrieve", "list"]:
            return ExamDetailSerialzer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        response = ExamDetailSerialzer(exam).data
        return Response(response)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exam = serializer.save()
        response = ExamDetailSerialzer(exam).data
        return Response(response)


# --------------------------------- SUBJECTS --------------------------------- #


class ExamSubjectViewSet(viewsets.ModelViewSet):
    queryset = ExamSubject.objects.all().select_related("exam", "subject")
    serializer_class = ExamSubjectSerializer
    http_method_names = ["post", "delete"]
    pagination_class = None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        exam_subject = serializer.save()
        response = ExamSubjectDetailSerializer(exam_subject).data
        return Response(response)


# ----------------------------- SUBJECT QUESTIONS ---------------------------- #


class ExamSubjectQuestionViewSet(viewsets.ModelViewSet):
    queryset = ExamSubjectQuestion.objects.all().select_related(
        "exam_subject", "question", "section", "subsection"
    )
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
        return Response(response)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        exam_subject_question = serializer.save()
        response = ExamSubjectQuestionSerializer(exam_subject_question).data
        return Response(response)
