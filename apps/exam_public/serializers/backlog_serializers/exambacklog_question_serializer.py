from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklogQuestion
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_attempt_response_serializer import (
    ExamBacklogQuestionAttemptResponseSerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_serializer import (
    ExamBacklogQuestionChoiceSerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_country_serializer import (
    ExamBacklogQuestionCountrySerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_media_serializer import (
    ExamBacklogQuestionMediaSerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_retryhint_serializer import (
    ExamBacklogQuestionRetryHintSerializer,
)
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_tag_serializer import (
    ExamBacklogQuestionTagSerializer,
)
from apps.exam_public.serializers.candidate_exam_answer_serializers import (
    CandidateExamQuestionAnswerSerializer,
)
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.lookups.serializers.tag_serializers import TagSerializer
from apps.questionbank.serializers.question_serializers.difficulty_level_serializers import (
    DifficultyLevelSerializer,
)
from apps.questionbank.serializers.question_serializers.question_type_serializers import (
    QuestionTypeSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class ExamBacklogQuestionSerializer(BaseModelSerializer):
    type = QuestionTypeSerializer()
    difficulty_level = DifficultyLevelSerializer()
    measuring_unit = MeasuringUnitSerializer()
    tags = serializers.SerializerMethodField()
    choices = serializers.SerializerMethodField()
    attempt_responses = serializers.SerializerMethodField()
    retry_hints = serializers.SerializerMethodField()
    medias = ExamBacklogQuestionMediaSerializer(many=True, source="exambacklogquestionmedia_set")
    countries = ExamBacklogQuestionCountrySerializer(many=True, source="exambacklogquestioncountry_set")
    question_answers = serializers.SerializerMethodField()

    class Meta:
        model = ExamBacklogQuestion
        fields = [
            "question_answers",
            "id",
            "subject_name",
            "education_level_name",
            "type",
            "title",
            "text",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "sequence",
            "time_limit",
            "total_marks",
            "difficulty_level",
            "measuring_unit",
            "is_optional",
            "is_global",
            "has_media",
            "medias",
            "choices",
            "attempt_responses",
            "retry_hints",
            "tags",
            "countries",
            "section_backlog",
            "subsection_backlog",
        ] + get_base_model_fields()

    def get_tags(self, obj):
        return ExamBacklogQuestionTagSerializer(obj.backlog_tags.all(), many=True).data

    def get_choices(self, obj):
        return ExamBacklogQuestionChoiceSerializer(obj.backlog_choices.all(), many=True).data

    def get_attempt_responses(self, obj):
        return ExamBacklogQuestionAttemptResponseSerializer(obj.backlog_attempt_responses, many=True).data

    def get_retry_hints(self, obj):
        return ExamBacklogQuestionRetryHintSerializer(obj.backlog_retry_hints.all(), many=True).data

    def get_question_answers(self, obj):
        # Use context to determine if answers should be included
        if self.context.get("get_answers", False):
            return CandidateExamQuestionAnswerSerializer(obj.question_answers.all(), many=True).data
        return None

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Remove the key if its value is None
        if not self.context.get("get_answers", False):
            representation.pop("question_answers")
        return representation
