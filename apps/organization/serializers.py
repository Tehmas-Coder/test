from rest_framework import serializers

from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.models import Organization
from apps.organization.models.organization_models import OrganizationUser
from apps.user.serializers.user_serializers import UserSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class OrganizationUserSerializer(BaseModelSerializer):

    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "user",
        ] + get_base_model_fields()


class OrganizationUserDetailSerializer(BaseModelSerializer):
    user = UserSerializer()

    class Meta:
        model = OrganizationUser
        fields = [
            "id",
            "organization",
            "user",
        ] + get_base_model_fields()


class OrganizationWithUsersListSerializer(serializers.ModelSerializer):
    organization_users = OrganizationUserDetailSerializer(many=True)
    organization_users_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
            "organization_users_count",
            "organization_users",
        ]

    def get_organization_users_count(self, obj):
        return obj.organization_users.count()


class CandidateWthoutOrganizationDetailSerializer(BaseModelSerializer):
    user = UserSerializer(required=True)

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()


class OrganizationWithCandidateListSerializer(serializers.ModelSerializer):
    organization_candidates = CandidateWthoutOrganizationDetailSerializer(many=True)
    organization_candidates_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = [
            "id",
            "name",
            "country",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
            "organization_candidates_count",
            "organization_candidates",
        ]

    def get_organization_candidates_count(self, obj):
        return obj.organization_candidates.count()
