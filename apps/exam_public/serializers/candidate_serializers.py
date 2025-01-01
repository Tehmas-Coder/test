from apps.exam_public.models.exam_public_models import Candidate
from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.lookups.serializers.organization_serializers import OrganizationSerializer
from apps.user.models.user_models import BaseUser
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

    def __init__(self, *args, **kwargs):
        self._context: dict = kwargs.get("context", {})
        if self._context.get("selector"):
            self.fields["user"] = UserSerializer(required=True)
            self.fields["organization"] = OrganizationSerializer(context={"mutator": True})
        super().__init__(*args, **kwargs)

    def create(self, validated_data):
        instance, _ = Candidate.objects.get_or_create(
            user=validated_data["user"],
            organization=validated_data["organization"],
            defaults=validated_data,
        )
        return instance


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
            "country",
            "phone",
            "user_candidates",
            "description",
            "created_at",
            "updated_at",
            "meta_status",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]
