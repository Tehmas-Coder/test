from apps.exam_public.models.exam_public_models import CandidateExamAnswer
from apps.lookups.serializers.media_serializers import MediaSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class CandidateExamAnswerEditSerializer(BaseModelSerializer):
    answer_files = MediaSerializer(many=True, required=False)

    class Meta:
        model = CandidateExamAnswer
        fields = [
            "candidate_exam",
            "exam_backlog_question",
            "exam_backlog_question_choice",
            "answer_text",
            "answer_files",
        ] + get_base_model_fields()

    def create(self, validated_data):
        # return super().create(validated_data)
        debug_print(validated_data)
        return True
