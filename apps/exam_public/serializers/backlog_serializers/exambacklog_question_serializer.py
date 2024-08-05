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
from apps.questionbank.serializers.question_serializers.question_type_serializers import (
    QuestionTypeSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionSerializer(BaseModelSerializer):
    type = QuestionTypeSerializer()
    # tags = ExamBacklogQuestionTagSerializer(many=True)
    # choices = ExamBacklogQuestionChoiceSerializer(many=True)
    # attempt_responses = ExamBacklogQuestionAttemptResponseSerializer(many=True)
    # retry_hints = ExamBacklogQuestionRetryHintSerializer(many=True)
    medias = ExamBacklogQuestionMediaSerializer(many=True, source="exambacklogquestionmedia_set")
    countries = ExamBacklogQuestionCountrySerializer(many=True, source="exambacklogquestioncountry_set")

    class Meta:
        model = ExamBacklogQuestion
        fields = [
            "id",
            "subject_name",
            "title",
            "type",
            "text",
            "max_retries",
            "retry_penalty",
            "can_shuffle",
            "has_media",
            "medias",
            # "choices",
            # "attempt_responses",
            # "retry_hints",
            # "tags",
            "countries",
        ] + get_base_model_fields()
