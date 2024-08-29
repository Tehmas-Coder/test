from rest_framework import serializers

from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.user.models import BaseUser
from apps.user.serializers.user_serializers import (
    UserDetailSerializer,
    UserEditSerializer,
)
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class OrganizationSerializer(BaseModelSerializer):
    users_count = serializers.SerializerMethodField()
    candidates_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "users_count",
            "candidates_count",
            "country",
        ] + get_base_model_fields()

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        country = instance.country
        if country:
            representation["country"] = CountrySerializer(country).data

        return representation

    def get_users_count(self, obj):
        return obj.organization_users.count()

    def get_candidates_count(self, obj):
        return obj.organization_candidates.count()


class OrganizationEditSerializer(BaseModelSerializer):

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
        ] + get_base_model_fields()

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
    user = UserEditSerializer()

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
