from rest_framework import serializers

from apps.exam_public.models.exam_public_backlog_models import ExamBacklog
from apps.exam_public.serializers.backlog_serializers.exambacklog_question_choice_serializer import (
    ExamBacklogQuestionChoiceForKeySerializer,
)
from core.serializers import BaseModelSerializer
from utils.rna_utils import debug_print


class ExamBacklogAnswersKeySerializer(BaseModelSerializer):
    questions_with_correct_choices = serializers.SerializerMethodField()

    class Meta:
        model = ExamBacklog
        fields = [
            "id",
            "questions_with_correct_choices",
        ]

    def get_questions_with_correct_choices(self, obj):
        questions = obj.backlog_questions.all()
        question_choices_hashmap = {one_question.id: one_question.backlog_choices.filter(is_correct=True) for one_question in questions}
        question_choices_hashmap = {key: value for key, value in question_choices_hashmap.items() if len(value)}
        response_list = [
            {"question_backlog_id": question_id, "correct_choices": ExamBacklogQuestionChoiceForKeySerializer(choices, many=True).data}
            for question_id, choices in question_choices_hashmap.items()
        ]

        return response_list
