from rest_framework import serializers

from apps.questionbank.models.question_models import QuestionAttemptResponse
from core.serializers import BaseModelSerializer, get_base_model_fields


class QuestionAttemptResponseSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionAttemptResponse
        fields = [
            "id",
            "question",
            "text",
            "type",
        ] + get_base_model_fields()
        read_only_fields = ["id"]

    def __init__(self, instance=None, data=..., **kwargs):
        self._context = kwargs.get("context", {})
        if self._context.get("exclude_question", False):
            self.fields.pop("question")
        if data != ...:
            super().__init__(instance, data, **kwargs)
        super().__init__(instance, **kwargs)


class QuestionAttemptResponseBulkCreateSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    responses = serializers.ListField(child=QuestionAttemptResponseSerializer(context={"exclude_question": True}))

    def validate(self, data):
        question_attempt_response_serializer_errors = []
        self.question_attempt_responses_instances_data = []

        for response in data.get("responses", []):
            question_attempt_response_data = {"question": data.get("question"), "type": response["type"], "text": response["text"]}
            question_attempt_response_serializer = QuestionAttemptResponseSerializer(data=question_attempt_response_data)
            if not question_attempt_response_serializer.is_valid():
                question_attempt_response_serializer_errors.append(question_attempt_response_serializer.errors)
            else:
                self.question_attempt_responses_instances_data.append(question_attempt_response_serializer.validated_data)

        if question_attempt_response_serializer_errors:
            raise serializers.ValidationError({"question_attempt_response_errors": question_attempt_response_serializer_errors})

        return data

    def create(self, validated_data):
        # * Bulk Create Question Attempt Responses
        question_attempt_responses_instances = [QuestionAttemptResponse(**data) for data in self.question_attempt_responses_instances_data]
        QuestionAttemptResponse.objects.bulk_create(question_attempt_responses_instances)
        created_question_attempt_responses_instances = QuestionAttemptResponse.objects.all().order_by("-created_at")[
            : len(question_attempt_responses_instances)
        ]
        created_question_attempt_responses_instances = sorted(created_question_attempt_responses_instances, key=lambda instance: instance.id)  # type: ignore
        return created_question_attempt_responses_instances
