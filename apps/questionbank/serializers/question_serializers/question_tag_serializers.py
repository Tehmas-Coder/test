from rest_framework import serializers
from core.serializers import BaseModelSerializer, get_base_model_fields
from apps.questionbank.models import QuestionTag
from utils.rna_utils import debug_print


class QuestionTagSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionTag
        fields = [
            "id",
            "question",
            "tag",
        ] + get_base_model_fields()


class QuestionTagBulkCreateSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        question_tag_serializer_errors = []
        self.question_tags_instances_data = []

        for tag in data.get("tags", []):
            question_tag_data = {"question": data.get("question"), "tag": tag}
            question_tag_serializer = QuestionTagSerializer(data=question_tag_data)
            if not question_tag_serializer.is_valid():
                question_tag_serializer_errors.append(question_tag_serializer.errors)
            else:
                self.question_tags_instances_data.append(question_tag_serializer.validated_data)

        if question_tag_serializer_errors:
            raise serializers.ValidationError({"question_tag_errors": question_tag_serializer_errors})

        return data

    def create(self, validated_data):
        # * Bulk Create Question Tags
        question_tags_instances = [QuestionTag(**data) for data in self.question_tags_instances_data]
        QuestionTag.objects.bulk_create(question_tags_instances)
        created_question_tags_instances = QuestionTag.objects.all().order_by("-created_at")[: len(question_tags_instances)]
        created_question_tags_instances = sorted(created_question_tags_instances, key=lambda instance: instance.id)

        return created_question_tags_instances
