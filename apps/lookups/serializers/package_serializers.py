from rest_framework import serializers

from apps.lookups.models.lookup_models import Package


class PackageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Package
        fields = [
            "id",
            "name",
            "abbreviation",
            "users",
            "questions",
            "exams",
            "prep_exams",
            "exam_attempts",
        ]
