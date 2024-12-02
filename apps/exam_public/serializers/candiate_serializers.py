from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.organization_serializers import (
    OrganizationEditSerializer,
    OrganizationSerializer,
)
from apps.user.models.user_models import BaseUser
from apps.user.serializers.role_permission_serializers import RoleSerializer
from apps.user.serializers.user_serializers import UserSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields


class CandidateSerializer(BaseModelSerializer):

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()

    def create(self, validated_data):
        instance, _ = Candidate.objects.get_or_create(
            user=validated_data["user"],
            organization=validated_data["organization"],
            defaults=validated_data,
        )

        return instance


class CandidateDetailSerializer(BaseModelSerializer):
    user = UserSerializer(required=True)
    organization = OrganizationEditSerializer()

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()


class CandidateWithOrganizationDetailSerializer(BaseModelSerializer):
    organization = OrganizationSerializer()

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()


class CandidateWithOrganizationsSerializer(BaseModelSerializer):

    roles = RoleSerializer(many=True, read_only=True, context={"mutator": True})
    country = CountrySerializer(read_only=True)
    user_candidates = CandidateWithOrganizationDetailSerializer(many=True)

    class Meta:
        model = BaseUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "full_name",
            "date_of_birth",
            "roles",
            "country",
            "phone",
            "user_candidates",
        ] + get_base_model_fields()
