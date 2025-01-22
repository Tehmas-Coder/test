from django.db.models import F
from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklog
from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.backlog_serializers.exam_backlog_serializers import (
    ExamBacklogDetailSerializer,
    ExamBacklogEditSerializer,
    ExamBacklogQuestionScoresheetSerializer,
)
from apps.exam_public.serializers.candidate_serializers import CandidateSerializer
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
            "start_datetime",
            "end_datetime",
            "exam_questions_visibility",
            "is_public",
            "is_preparatory",
        ] + get_base_model_fields()

    def create(self, validated_data):
        organization_id = self.initial_data.get("organization_id")  # type: ignore
        # * Fetching candidates instances for candidates_ids in request data, creating new instances of candidates with this organization if those candidates already exist but with any other organization
        candidates = validated_data.pop("candidates")
        candidates_instances = list(Candidate.objects.filter(user__email__in=candidates))
        list_of_user_ids_in_candidates_instances = list(set([one_candidate.user_id for one_candidate in candidates_instances]))  # type: ignore

        for one_candidate in candidates_instances:
            if one_candidate.organization_id == organization_id and (one_candidate.user_id in list_of_user_ids_in_candidates_instances):  # type: ignore
                list_of_user_ids_in_candidates_instances.remove(one_candidate.user_id)  # type: ignore

        Candidate.objects.bulk_create(
            [Candidate(user_id=user_id, organization_id=organization_id) for user_id in list_of_user_ids_in_candidates_instances]
        )
        candidates_instances = list(
            Candidate.objects.filter(user__email__in=candidates, organization_id=organization_id).annotate(email=F("user__email"))
        )
        email_in_candidate_instances = [one_candidate.email for one_candidate in candidates_instances]  # type: ignore

        # * Setting up data to be fetched from schedule model
        schedule = validated_data.get("schedule")
        if schedule:
            validated_data["start_datetime"] = schedule.start_datetime
            validated_data["end_datetime"] = schedule.end_datetime
            related_data_for_creation = {
                "waiting_duration": schedule.waiting_duration,
                "extra_duration": schedule.extra_duration,
            }
            validated_data.update(related_data_for_creation)

        # * Setting organization_id
        validated_data["organization_id"] = organization_id

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
    candidate = CandidateSerializer(required=False, context={"selector": True})
    exam_backlog = ExamBacklogEditSerializer()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "exam_questions_visibility",
            "is_public",
            "is_preparatory",
            "total_obtainable_marks",
            "obtained_marks",
            "exam_result",
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

        read_only_fields = ["exam_result"]


class CandidateExamDetailSerializer(BaseModelSerializer):
    candidate = CandidateSerializer(required=False, context={"selector": True})
    exam_backlog = serializers.SerializerMethodField()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "exam_questions_visibility",
            "is_public",
            "is_preparatory",
            "total_obtainable_marks",
            "obtained_marks",
            "exam_duration",
            "exam_result",
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

        read_only_fields = ["exam_result"]

    def __init__(self, *args, **kwargs):
        context = kwargs.pop("context", False)
        get_retry_hints = context.pop("get_retry_hints", True)
        super().__init__(*args, **kwargs)
        self.context["get_retry_hints"] = get_retry_hints

    def get_exam_backlog(self, obj):
        return ExamBacklogDetailSerializer(obj.exam_backlog, context=self.context).data


class ExamBacklogWithCandidateDetailsSerializer(BaseModelSerializer):
    candidate_exam_examsbacklog = CandidateExamListSerializer(many=True)

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
            "passing_percentage",
            "is_global",
            "candidate_exam_examsbacklog",
        ] + get_base_model_fields()


class CandidateExamWithAnswersDetailSerializer(BaseModelSerializer):
    candidate = CandidateSerializer(required=False, context={"selector": True})
    exam_backlog = serializers.SerializerMethodField()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "exam_questions_visibility",
            "is_public",
            "is_preparatory",
            "total_obtainable_marks",
            "obtained_marks",
            "exam_result",
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

        read_only_fields = ["exam_result"]

    def __init__(self, *args, **kwargs):
        context = kwargs.pop("context", False)
        get_answers = context.pop("get_answers", False)
        get_retry_hints = context.pop("get_retry_hints", True)
        super().__init__(*args, **kwargs)
        self.context["get_answers"] = get_answers
        self.context["get_retry_hints"] = get_retry_hints

    def get_exam_backlog(self, obj):
        return ExamBacklogDetailSerializer(obj.exam_backlog, context=self.context).data


# ------------------- Candidate Exam Scoresheet Serializer ------------------- #


class CandidateExamScoresheetSerializer(BaseModelSerializer):
    exam_backlog = serializers.SerializerMethodField()

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "exam_questions_visibility",
            "is_public",
            "is_preparatory",
            "total_obtainable_marks",
            "obtained_marks",
            "exam_result",
            "exam_duration",
            "schedule",
            "start_datetime",
            "end_datetime",
            "waiting_duration",
            "extra_duration",
            "exam_status",
            "candidate_email",
            "exam_backlog",
        ] + get_base_model_fields()

        read_only_fields = ["exam_result"]

    def get_exam_backlog(self, obj):
        return ExamBacklogQuestionScoresheetSerializer(obj.exam_backlog).data
