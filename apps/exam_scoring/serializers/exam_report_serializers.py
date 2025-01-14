from rest_framework import serializers

from apps.exam_public.models.exam_public_models import CandidateExam


class ExamReportSerializer(serializers.ModelSerializer):
    candidate_exam_id = serializers.UUIDField(source="id")
    candidate_first_name = serializers.CharField(source="candidate.user.first_name", allow_null=True)
    candidate_last_name = serializers.CharField(source="candidate.user.last_name", allow_null=True)
    exam_backlog_name = serializers.CharField(source="exam_backlog.name")
    total_marks = serializers.FloatField(source="exam_backlog.total_marks")
    passing_percentage = serializers.IntegerField(source="exam_backlog.passing_percentage")

    class Meta:
        model = CandidateExam
        fields = [
            "candidate_exam_id",
            "candidate_first_name",
            "candidate_last_name",
            "candidate_email",
            "exam_backlog_name",
            "start_datetime",
            "end_datetime",
            "exam_status",
            "total_marks",
            "total_obtainable_marks",
            "passing_percentage",
            "obtained_marks",
            "exam_result",
        ]
