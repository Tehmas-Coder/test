from apps.exam_public.models.exam_public_models import Candidate, CandidateExam
from apps.exam_public.serializers.candiate_serializers import CandidateDetailSerializer
from apps.user.serializers.user_serializers import UserDetailSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class CandidateExamSerializer(BaseModelSerializer):

    class Meta:
        model = CandidateExam
        fields = [
            "id",
            "candidate",
            "exam",
            "schedule",
            "obtained_marks",
        ] + get_base_model_fields()

    def create(self, validated_data):
        data_for_creation = {
            "obtained_marks": 0,
            "education_level": validated_data.get("exam").education_level,
            "name": validated_data.get("exam").name,
            "code": validated_data.get("exam").code,
            "abbreviation": validated_data.get("exam").abbreviation,
            "instructions": validated_data.get("exam").instructions,
            "total_marks": validated_data.get("exam").total_marks,
            "pass_marks": validated_data.get("exam").pass_marks,
            "is_global": validated_data.get("exam").is_global,
            "date": validated_data.get("schedule").date,
            "start_time": validated_data.get("schedule").start_time,
            "end_time": validated_data.get("schedule").end_time,
            "waiting_duration": validated_data.get("schedule").waiting_duration,
            "extra_duration": validated_data.get("schedule").extra_duration,
        }
        validated_data.update(data_for_creation)
        return super().create(validated_data)


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
