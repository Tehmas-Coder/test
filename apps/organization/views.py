from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.organization.models.organization_models import Organization
from apps.organization.serializers import (
    OrganizationSerializer,
    OrganizationUserSerializer,
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
