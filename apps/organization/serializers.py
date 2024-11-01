from rest_framework import serializers

from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.models import Organization
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.package_serializers import PackageSerializer
from apps.organization.models.organization_models import (
    OrganizationPackage,
    OrganizationUser,
)
from apps.user.serializers.user_serializers import UserDetailSerializer
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


class OrganizationSerializer(BaseModelSerializer):
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
        ] + get_base_model_fields()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        country = instance.country
        if country:
            representation["country"] = CountrySerializer(country).data

        return representation


class OrganizationEditSerializer(BaseModelSerializer):
    package = serializers.IntegerField(required=False)

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "package",
        ] + get_base_model_fields()

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


class OrganizationUserSerializer(BaseModelSerializer):

    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "user",
        ] + get_base_model_fields()


class OrganizationUserDetailSerializer(BaseModelSerializer):
    user = UserDetailSerializer()

    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "user",
        ] + get_base_model_fields()


class OrganizationWithUsersListSerializer(BaseModelSerializer):
    organization_users = OrganizationUserDetailSerializer(many=True)
    organization_users_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "organization_users_count",
            "organization_users",
        ] + get_base_model_fields()

    def get_organization_users_count(self, obj):
        return obj.organization_users.count()


class CandidateWthoutOrganizationDetailSerializer(BaseModelSerializer):
    user = UserDetailSerializer(required=True)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()


class OrganizationWithCandidateListSerializer(BaseModelSerializer):
    organization_candidates = CandidateWthoutOrganizationDetailSerializer(many=True)
    organization_candidates_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "organization_candidates_count",
            "organization_candidates",
        ] + get_base_model_fields()

    def get_organization_candidates_count(self, obj):
        return obj.organization_candidates.count()
