from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.serializers import OrganizationSerializer
from apps.user.serializers.user_serializers import UserDetailSerializer
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
    user = UserDetailSerializer(required=True)
    organization = OrganizationSerializer()

    class Meta:
        model = Candidate
        fields = [
            "id",
            "user",
            "organization",
        ] + get_base_model_fields()
