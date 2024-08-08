from apps.exam_public.models.exam_public_models import CandidateExamAnswer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CandidateExamAnswerEditSerializer(BaseModelSerializer):
    class Meta:
        model = CandidateExamAnswer
        fields = [
            "candidate_exam",
            "exam_backlog_question",
            "exam_backlog_question_choice",
            "answer_text",
            "answer_files",
            "score",
            "is_correct",
            "seconds_taken",
        ] + get_base_model_fields()
