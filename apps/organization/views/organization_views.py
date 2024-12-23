from django.db.models import Count, F, Prefetch
from rest_framework import status, viewsets
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.exam_public.serializers.candidate_serializers import (
    CandidateWithOrganizationsSerializer,
)
from apps.lookups.models.lookup_models import Organization
from apps.organization.models.organization_models import OrganizationUser
from apps.organization.serializers.organization_serializers import (
    OrganizationWithCandidateListSerializer,
    OrganizationWithUsersListSerializer,
)
from apps.user.models.user_models import BaseUser
from middlewares.current_user_middleware import get_current_user
from utils.rna_utils import make_error_response


class OrganizationRelatedViewset(viewsets.ViewSet):

    def get_organization_users_list(self, request, *args, **kwargs):
        organization_id = kwargs.get("id")
        filtered_organization = Organization.get_detailed_queryset(organization_users=True).filter(id=organization_id).first()
        response_data = OrganizationWithUsersListSerializer(filtered_organization).data if filtered_organization else {}
        return Response(response_data, status=status.HTTP_200_OK)

    def get_organization_candidates_list(self, request, *args, **kwargs):
        organization_id = kwargs.get("id")
        organization = Organization.get_detailed_queryset(organization_candidates=True).filter(id=organization_id).first()
        organization_with_candidates_list = OrganizationWithCandidateListSerializer(organization).data if organization else {}
        return Response(organization_with_candidates_list, status=status.HTTP_200_OK)

    def get_candidate_organizations_list(self, request, *args, **kwargs):
        candidate_with_organizations_instance = (
            BaseUser.objects.filter(id=get_current_user().id)  # type: ignore
            .select_related("country")
            .prefetch_related(
                Prefetch(
                    "user_candidates",
                    queryset=Candidate.objects.select_related("organization", "organization__country")
                    .prefetch_related(
                        "organization__organization_packages",
                        "organization__organization_packages__package",
                    )
                    .all(),
                )
            )
            .first()
        )
        if not candidate_with_organizations_instance:
            return make_error_response(message="Candidate not found")
        else:
            candidate_organizations_data_response = CandidateWithOrganizationsSerializer(candidate_with_organizations_instance).data
        return Response(candidate_organizations_data_response, status=status.HTTP_200_OK)

    def get_user_organizations_list(self, request, *args, **kwargs):
        user_organization_detail = list(
            (
                OrganizationUser.objects.filter(user_id=get_current_user().id)  # type: ignore
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
