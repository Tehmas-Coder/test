from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.candiate_serializers import CandidateDetailSerializer
from apps.user.serializers.user_serializers import UserDetailSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CandidateExamSerializer(BaseModelSerializer):

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidate",
            "exam",
            "schedule",
            "obtained_marks",
            "education_level",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "total_marks",
            "pass_marks",
            "date",
            "start_time",
            "end_time",
            "waiting_duration",
            "extra_duration",
            "is_global",
        ] + get_base_model_fields()


class CandidateExamDetailSerializer(BaseModelSerializer):
    candidate = CandidateDetailSerializer(required=True)

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidate",
            "exam",
            "schedule",
            "obtained_marks",
            "education_level",
            "name",
            "code",
            "abbreviation",
            "instructions",
            "total_marks",
            "pass_marks",
            "date",
            "start_time",
            "end_time",
            "waiting_duration",
            "extra_duration",
            "is_global",
        ] + get_base_model_fields()
