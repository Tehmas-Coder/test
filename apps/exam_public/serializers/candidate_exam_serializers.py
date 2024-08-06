from rest_framework import serializers

from apps.exam_admin.serializers.exam_serializers import ExamDetailSerializer
from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogDetailSerializer,
)
from apps.exam_public.serializers.candiate_serializers import CandidateDetailSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class CandidateExamEditSerializer(BaseModelSerializer):
    candidates = serializers.ListField(child=serializers.IntegerField())

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidates",
            "exam_backlog",
            "schedule",
        ] + get_base_model_fields()

    def create(self, validated_data):
        # * Fetching candidates instances for candidates_ids in request data
        candidates = validated_data.pop("candidates")
        candidates_instances = list(Candidate.objects.filter(pk__in=candidates))

        # * Setting up data to be fetched from schedule model
        schedule = validated_data.get("schedule")
        related_data_for_creation = {
            "date": schedule.date,
            "start_time": schedule.start_time,
            "end_time": schedule.end_time,
            "waiting_duration": schedule.waiting_duration,
            "extra_duration": schedule.extra_duration,
        }
        validated_data.update(related_data_for_creation)

        # * CandidateExam bulk create
        bulk_create_instances_list = []
        for one_instance in candidates_instances:
            bulk_create_instances_list.append(CandidateExam(candidate=one_instance, **validated_data))

        CandidateExam.objects.bulk_create(bulk_create_instances_list)

        return bulk_create_instances_list


class CandidateExamListSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=True)

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidate",
            "exam_backlog",
            "schedule",
            "obtained_marks",
            "date",
            "start_time",
            "end_time",
            "waiting_duration",
            "extra_duration",
        ] + get_base_model_fields()


class CandidateExamDetailSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=True)
    exam_backlog = ExamBacklogDetailSerializer(required=True)

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidate",
            "exam_backlog",
            "schedule",
            "obtained_marks",
            "date",
            "start_time",
            "end_time",
            "waiting_duration",
            "extra_duration",
        ] + get_base_model_fields()
