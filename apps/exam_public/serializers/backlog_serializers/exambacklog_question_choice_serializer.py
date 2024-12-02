from apps.exam_public.models.exam_public_backlog_models import ExamBacklogQuestionChoice
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_media_serializer import (
    ExamBacklogQuestionChoiceMediaSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields


class ExamBacklogQuestionChoiceSerializer(BaseModelSerializer):
    medias = ExamBacklogQuestionChoiceMediaSerializer(many=True, required=False, source="exambacklogquestionchoicemedia_set")

    class Meta:
        model = ExamBacklogQuestionChoice
        fields = [
            "id",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
            "has_media",
            "medias",
        ] + get_base_model_fields()

        read_only_fields = ["id"]


class ExamBacklogQuestionChoiceForNonPreparatorySerializer(BaseModelSerializer):
    medias = ExamBacklogQuestionChoiceMediaSerializer(many=True, required=False, source="exambacklogquestionchoicemedia_set")

    class Meta:
        model = ExamBacklogQuestionChoice
        fields = [
            "id",
            "title",
            "text",
            "has_media",
            "medias",
        ] + get_base_model_fields()

        read_only_fields = ["id"]


class ExamBacklogQuestionChoiceForKeySerializer(BaseModelSerializer):

    class Meta:
        model = ExamBacklogQuestionChoice
        fields = [
            "id",
            "title",
            "text",
            "weight",
            "is_negative_weight",
            "is_correct",
        ]
