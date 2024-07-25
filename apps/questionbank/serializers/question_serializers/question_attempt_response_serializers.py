from apps.questionbank.models import QuestionAttemptResponse
from core.serializers import BaseModelSerializer, get_base_model_fields
from rest_framework import serializers


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


class QuestionAttemptResponseEditSerializer(BaseModelSerializer):

    class Meta:
        model = QuestionAttemptResponse
        fields = [
            "id",
            "text",
            "type",
        ] + get_base_model_fields()
        read_only_fields = ["id"]


class QuestionAttemptResponseBulkCreateSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    responses = serializers.ListField(child=QuestionAttemptResponseEditSerializer())

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

        return created_question_attempt_responses_instances
