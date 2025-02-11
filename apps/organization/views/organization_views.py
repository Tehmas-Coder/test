from django.db.models import F
from rest_framework import status, viewsets
from rest_framework.response import Response

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
        is_self_preparation = bool(request.query_params.get("is_self_preparation", False))
        candidate_with_organizations_instance = (
            BaseUser.get_detail_queryset(country=True, user_candidates=True).filter(id=get_current_user().id).first()  # type: ignore
        )
        if not candidate_with_organizations_instance:
            return make_error_response(message="Candidate not found")
        else:
            response_data = CandidateWithOrganizationsSerializer(candidate_with_organizations_instance).data

        if is_self_preparation:
            user_candidate__instances = response_data.get("user_candidates", [])
            response_data = [candidate["organization"] for candidate in user_candidate__instances if candidate.get("is_self_preparation_allowed")]
        return Response(response_data, status=status.HTTP_200_OK)

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
