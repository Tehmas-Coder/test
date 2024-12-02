from rest_framework import serializers

from apps.lookups.models.lookup_models import Organization
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.package_serializers import PackageSerializer
from apps.organization.models.organization_models import OrganizationPackage
from core.serializers import BaseModelSerializer, get_base_model_fields


class OrganizationPackageSerializer(BaseModelSerializer):
    package = PackageSerializer()

    class Meta:
        model = OrganizationPackage
        fields = [
            "id",
            "organization",
            "package",
            "users",
            "questions",
            "exams",
            "prep_exams",
            "exam_attempts",
        ] + get_base_model_fields()


class OrganizationSerializer(serializers.ModelSerializer):
    users_count = serializers.IntegerField(read_only=True)
    candidates_count = serializers.IntegerField(read_only=True)
    organization_packages = OrganizationPackageSerializer(many=True)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "users_count",
            "candidates_count",
            "country",
            "organization_packages",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        country = instance.country
        if country:
            representation["country"] = CountrySerializer(country).data

        return representation


class OrganizationEditSerializer(serializers.ModelSerializer):
    package = serializers.IntegerField(required=False)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "package",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
        ]

    def create(self, validated_data):
        package = validated_data.pop("package")
        organization = super().create(validated_data)
        OrganizationPackage.objects.create(organization=organization, package_id=package)
        return organization

    def update(self, instance, validated_data):
        package = validated_data.pop("package", None)
        if package is not None:
            OrganizationPackage.objects.get(organization=instance).delete()
            OrganizationPackage.objects.create(organization=instance, package_id=package)
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        country = instance.country
        if country:
            representation["country"] = CountrySerializer(country).data

        return representation
