from django.db.models import F, Prefetch
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.exam_public.serializers.candiate_serializers import (
    CandidateWithOrganizationsSerializer,
)
from apps.lookups.models.lookup_models import Organization
from apps.organization.models.organization_models import OrganizationUser
from apps.organization.serializers.organization_serializers import (
    OrganizationWithCandidateListSerializer,
    OrganizationWithUsersListSerializer,
)
from apps.user.models.user_models import BaseUser
from utils.rna_utils import make_error_response


class OrganizationRelatedViewset(viewsets.ViewSet):

    def get_organization_users_list(self, request, *args, **kwargs):
        organization_id = kwargs.get("id", None)
        filtered_organization = Organization.get_detailed_queryset(organization_users=True).filter(id=organization_id).first()
        response_data = (
            OrganizationWithUsersListSerializer(
                filtered_organization,
            ).data
            if filtered_organization
            else {}
        )
        return Response(response_data, status=status.HTTP_200_OK)

    def get_organization_candidates_list(self, request, *args, **kwargs):
        organization_id = kwargs.get("id")
        if not organization_id:
            return make_error_response(message="Organization ID is required.")
        organization = Organization.get_detailed_queryset(organization_candidates=True).filter(id=organization_id).first()
        organization_with_candidates_list = OrganizationWithCandidateListSerializer(organization).data if organization else {}
        return Response(organization_with_candidates_list, status=status.HTTP_200_OK)

    def get_candidate_organizations_list(self, request, *args, **kwargs):

        filtered_candidate_queryset = CandidateWithOrganizationsSerializer(
            BaseUser.objects.filter(id=request.user.id).prefetch_related("user_candidates"), many=True
        ).data
        filtered_candidate_queryset_response = {}
        if len(filtered_candidate_queryset):
            filtered_candidate_queryset_response = filtered_candidate_queryset[0]

        return Response(filtered_candidate_queryset_response, status=status.HTTP_200_OK)

    def get_user_organizations_list(self, request, *args, **kwargs):

        user_organization_detail = list(
            (
                OrganizationUser.objects.filter(user_id=request.user.id)
                .select_related(
                    "organization",
                    "organization__country",
                )
                .annotate(
                    organization_name=F("organization__name"),
                    organization_country=F("organization__country_id"),
                    organization_country_name=F("organization__country__name"),
                )
                .values()
            )
        )

        return Response(user_organization_detail, status=status.HTTP_200_OK)
