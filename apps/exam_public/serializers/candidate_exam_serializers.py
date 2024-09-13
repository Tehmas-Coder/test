from django.db.models import F
from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklog
from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogDetailSerializer,
    ExamBacklogEditSerializer,
)
from apps.exam_public.serializers.candiate_serializers import CandidateDetailSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CandidateExamEditSerializer(BaseModelSerializer):
    candidates = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidates",
            "exam_backlog",
            "exam_duration",
            "schedule",
            "is_preparatory",
        ] + get_base_model_fields()

    def create(self, validated_data):
        # * Fetching candidates instances for candidates_ids in request data
        candidates = validated_data.pop("candidates")
        candidates_instances = list(Candidate.objects.filter(user__email__in=candidates).select_related("user").annotate(email=F("user__email")))
        email_in_candidate_instances = [one_candidate.email for one_candidate in candidates_instances]  # type: ignore

        # * Setting up data to be fetched from schedule model
        schedule = validated_data.get("schedule")
        related_data_for_creation = {
            "start_datetime": schedule.start_datetime,
            "end_datetime": schedule.end_datetime,
            "waiting_duration": schedule.waiting_duration,
            "extra_duration": schedule.extra_duration,
        }
        validated_data.update(related_data_for_creation)

        # * CandidateExam bulk create
        bulk_create_instances_list = []
        for one_instance in candidates_instances:
            bulk_create_instances_list.append(CandidateExam(candidate=one_instance, candidate_email=one_instance.email, **validated_data))  # type: ignore

        for one_candidate_email in candidates:
            if one_candidate_email not in email_in_candidate_instances:
                bulk_create_instances_list.append(CandidateExam(candidate_email=one_candidate_email, **validated_data))

        CandidateExam.objects.bulk_create(bulk_create_instances_list)

        return bulk_create_instances_list


class CandidateExamListSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=False)
    exam_backlog = ExamBacklogEditSerializer()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "is_preparatory",
            "total_obtainable_marks",
            "exam_duration",
            "schedule",
            "start_datetime",
            "end_datetime",
            "waiting_duration",
            "extra_duration",
            "exam_status",
            "candidate_email",
            "candidate",
            "exam_backlog",
        ] + get_base_model_fields()


class CandidateExamDetailSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=False)
    exam_backlog = serializers.SerializerMethodField()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "is_preparatory",
            "total_obtainable_marks",
            "exam_duration",
            "schedule",
            "start_datetime",
            "end_datetime",
            "waiting_duration",
            "extra_duration",
            "exam_status",
            "candidate_email",
            "candidate",
            "exam_backlog",
        ] + get_base_model_fields()

    def __init__(self, *args, **kwargs):
        context = kwargs.pop("context", False)
        get_retry_hints = context.pop("get_retry_hints", True)
        super().__init__(*args, **kwargs)
        self.context["get_retry_hints"] = get_retry_hints

    def get_exam_backlog(self, obj):
        return ExamBacklogDetailSerializer(obj.exam_backlog, context=self.context).data


class ExamBacklogWithCandidateDetailsSerializer(BaseModelSerializer):
    candiate_exam_examsbacklog = CandidateExamListSerializer(many=True)

    class Meta:
        model = ExamBacklog
        fields = [
            "id",
            "exam",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "education_level",
            "education_level_name",
            "total_marks",
            "pass_marks",
            "is_global",
            "candiate_exam_examsbacklog",
        ] + get_base_model_fields()


class CandidateExamWithAnswersDetailSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=False)
    exam_backlog = serializers.SerializerMethodField()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "is_preparatory",
            "total_obtainable_marks",
            "obtained_marks",
            "exam_duration",
            "schedule",
            "start_datetime",
            "end_datetime",
            "waiting_duration",
            "extra_duration",
            "exam_status",
            "candidate_email",
            "candidate",
            "exam_backlog",
        ] + get_base_model_fields()

    def __init__(self, *args, **kwargs):
        context = kwargs.pop("context", False)
        get_answers = context.pop("get_answers", False)
        get_retry_hints = context.pop("get_retry_hints", True)
        super().__init__(*args, **kwargs)
        self.context["get_answers"] = get_answers
        self.context["get_retry_hints"] = get_retry_hints

    def get_exam_backlog(self, obj):
        return ExamBacklogDetailSerializer(obj.exam_backlog, context=self.context).data
