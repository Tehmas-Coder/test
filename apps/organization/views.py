from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.exam_public.serializers.candiate_serializers import (
    CandidateWithOrganizationsSerializer,
)
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.organization.serializers import (
    OrganizationSerializer,
    OrganizationUserSerializer,
    OrganizationWithCandidateListSerializer,
    OrganizationWithUsersListSerializer,
)
from apps.user.models import BaseUser
from utils.rna_utils import debug_print


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all().select_related("country")
    serializer_class = OrganizationSerializer
    pagination_class = None
    http_method_names = ["get", "post", "patch", "delete"]

    @action(detail=False, methods=["post"], url_path="assign-organization-user")
    def assign_organization_user(self, request):
        serializer = OrganizationUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class OrganizationRelatedViewset(viewsets.ViewSet):

    def get_organization_users_list(self, request, *args, **kwargs):
        logged_in_user = self.request.user
        organization_id = kwargs.get("id", None)

        organization_queryset = Organization.objects.all()

        filtered_organization_queryset = []
        if logged_in_user.is_superuser:
            filtered_organization_queryset = organization_queryset
        else:
            filtered_organization_queryset = organization_queryset.filter(id=organization_id)

        organization_list = OrganizationWithUsersListSerializer(
            filtered_organization_queryset.prefetch_related(
                Prefetch(
                    "organization_users",
                    OrganizationUser.objects.all()
                    .select_related(
                        "user",
                        "user__country",
                    )
                    .prefetch_related("user__roles"),
                )
            ),
            many=True,
        ).data

        if logged_in_user.is_superuser == None:
            if not len(organization_list):
                return Response([], status=status.HTTP_200_OK)
            return Response(organization_list[0], status=status.HTTP_200_OK)

        return Response(organization_list, status=status.HTTP_200_OK)

    def get_organization_candidates_list(self, request, *args, **kwargs):
        logged_in_user = self.request.user
        organization_id = kwargs.get("id", None)

        organization_queryset = Organization.objects.all()

        filtered_organization_queryset = []
        if logged_in_user.is_superuser:
            filtered_organization_queryset = organization_queryset
        else:
            filtered_organization_queryset = organization_queryset.filter(id=organization_id)

        organization_with_candidates_list = OrganizationWithCandidateListSerializer(
            filtered_organization_queryset.prefetch_related(
                Prefetch(
                    "organization_candidates",
                    Candidate.objects.all()
                    .select_related(
                        "user",
                        "user__country",
                    )
                    .prefetch_related("user__roles"),
                )
            ),
            many=True,
        ).data

        if logged_in_user.is_superuser == None:
            if not len(organization_with_candidates_list):
                return Response([], status=status.HTTP_200_OK)
            return Response(organization_with_candidates_list[0], status=status.HTTP_200_OK)

        return Response(organization_with_candidates_list, status=status.HTTP_200_OK)

    def get_candidate_organizations_list(self, request, *args, **kwargs):

        filtered_candidate_queryset = CandidateWithOrganizationsSerializer(
            BaseUser.objects.filter(id=self.request.user.id).prefetch_related("user_candidates"), many=True
        ).data
        filtered_candidate_queryset_response = {}
        if len(filtered_candidate_queryset):
            filtered_candidate_queryset_response = filtered_candidate_queryset[0]

        return Response(filtered_candidate_queryset_response, status=status.HTTP_200_OK)
