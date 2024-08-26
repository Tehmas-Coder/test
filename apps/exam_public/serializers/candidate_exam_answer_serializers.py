from apps.exam_public.models.exam_public_models import (
    CandidateExam,
    CandidateExamAnswer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_serializer import (
    ExamBacklogQuestionChoiceSerializer,
)
from apps.exam_public.serializers.candiate_serializers import CandidateDetailSerializer
from apps.lookups.serializers.media_serializers import MediaSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class CandidateExamAnswerSerializer(BaseModelSerializer):
    answer_files = MediaSerializer(many=True, required=False)

    class Meta:
        model = CandidateExamAnswer
        fields = [
            "id",
            "candidate_exam",
            "exam_backlog_question",
            "exam_backlog_question_choice",
            "answer_text",
            "answer_files",
            "score",
            "is_correct",
        ] + get_base_model_fields()


class CandidateExamQuestionAnswerSerializer(BaseModelSerializer):
    answer_files = MediaSerializer(many=True, required=False)
    exam_backlog_question_choice = ExamBacklogQuestionChoiceSerializer(required=False)

    class Meta:
        model = CandidateExamAnswer
        fields = [
            "id",
            "exam_backlog_question_choice",
            "answer_text",
            "answer_files",
            "score",
            "is_correct",
        ] + get_base_model_fields()
