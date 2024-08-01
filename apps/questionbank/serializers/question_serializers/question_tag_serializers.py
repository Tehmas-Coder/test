from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import serializers

from apps.lookups.models import Tag
from apps.questionbank.models import Question, QuestionTag
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import color_print, debug_print


class QuestionTagSerializer(BaseModelSerializer):
    class Meta:
        model = QuestionTag
        fields = [
            "id",
            "question",
            "tag",
        ] + get_base_model_fields()


class QuestionTagBulkUpsertSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    tags = serializers.ListField(child=serializers.IntegerField())

    def validate(self, data):
        input_tag_ids = data.get("tags", [])

        tag_instances = list(Tag.objects.filter(pk__in=input_tag_ids))

        if len(tag_instances) != len(input_tag_ids):
            raise serializers.ValidationError({"tag_erros": "Unexpected tag id recieved."})

        question_instance = get_object_or_404(Question, pk=data.get("question"))

        existing_tag_ids = list(QuestionTag.objects.filter(question=question_instance).values_list("tag_id", flat=True))
        to_delete = []
        self.to_create = []

        for tag in tag_instances:
            if tag.id not in existing_tag_ids:  # type: ignore
                self.to_create.append({"question": question_instance, "tag": tag})

        for tag_id in existing_tag_ids:
            if tag_id not in input_tag_ids:
                to_delete.append(tag_id)

        QuestionTag.objects.filter(tag_id__in=to_delete).delete()

        return data

    def create(self, validated_data):
        # * Bulk Upsert Question Tags
        question_tags_instances = [QuestionTag(**data) for data in self.to_create]
        QuestionTag.objects.bulk_create(question_tags_instances)
        question_tag_instances = QuestionTag.objects.filter(question=validated_data["question"])

        return question_tag_instances
