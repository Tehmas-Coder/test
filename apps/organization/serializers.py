from rest_framework import serializers

from apps.lookups.serializers.country_serializers import CountrySerializer
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.user.models import BaseUser
from apps.user.serializers.user_serializers import UserEditSerializer
from core.serializers import BaseModelSerializer, get_base_model_fields
from utils.rna_utils import debug_print


class OrganizationSerializer(BaseModelSerializer):

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
