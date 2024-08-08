from django.db.models import Prefetch
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.exam_public.models.exam_public_models import Candidate
from apps.organization.models.organization_models import Organization, OrganizationUser
from apps.organization.serializers import (
    OrganizationSerializer,
    OrganizationUserSerializer,
    OrganizationWithCandidateListSerializer,
    OrganizationWithUsersListSerializer,
)


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

    def get_orgaization_users_list(self, request, *args, **kwargs):
        organization_list = OrganizationWithUsersListSerializer(
            Organization.objects.all().prefetch_related(
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

        return Response(organization_list, status=status.HTTP_200_OK)

    def get_orgaization_candidates_list(self, request, *args, **kwargs):
        organization_list = OrganizationWithCandidateListSerializer(
            Organization.objects.all().prefetch_related(
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

        return Response(organization_list, status=status.HTTP_200_OK)
