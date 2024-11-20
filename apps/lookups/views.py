from django.db.models import Count, Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.lookups.custom.lookups_classes import (
    OrganizationResourceQuerysetMutator,
    OrganizationResourceValidator,
)
from apps.lookups.models import (
    Country,
    Currency,
    Language,
    MeasuringUnit,
    MediaType,
    Organization,
    Package,
    Region,
    State,
    Timezone,
)
from apps.lookups.serializers.country_serializers import (
    CountryDetailSerializer,
    CountrySerializer,
)
from apps.lookups.serializers.currency_serializers import CurrencySerializer
from apps.lookups.serializers.language_serializers import LanguageSerializer
from apps.lookups.serializers.measuring_unit_serializers import MeasuringUnitSerializer
from apps.lookups.serializers.media_type_serializers import MediaTypeSerializer
from apps.lookups.serializers.organization_serializers import (
    OrganizationEditSerializer,
    OrganizationSerializer,
)
from apps.lookups.serializers.package_serializers import PackageSerializer
from apps.lookups.serializers.region_serializers import RegionDetailSerializer
from apps.lookups.serializers.state_serializers import StateSerializer
from apps.lookups.serializers.timezone_serializers import TimezoneSerializer
from apps.organization.filters.organization_filters import OrganizationFilterBackend
from apps.organization.models.organization_models import OrganizationUser
from apps.organization.serializers import OrganizationUserSerializer
from apps.questionbank.models import Tag
from apps.questionbank.serializers.tag_serializers import TagSerializer
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from utils.rna_utils import make_error_response


class TimezoneViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    pagination_class = None
    serializer_class = TimezoneSerializer
    queryset = Timezone.objects.all()
    pagination_class = None


class RegionViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = RegionDetailSerializer
    queryset = Region.objects.all().prefetch_related("countries")
    pagination_class = None


class CountryViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = CountryDetailSerializer
    queryset = Country.get_detail_queryset()
    pagination_class = None
    permission_classes = []

    def get_serializer(self, *args, **kwargs):
        if self.action == "list":
            return CountrySerializer(*args, **kwargs)
        return super().get_serializer(*args, **kwargs)


class StateViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = StateSerializer
    queryset = State.objects.all()
    pagination_class = None


class LanguageViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = LanguageSerializer
    queryset = Language.objects.all()
    pagination_class = None


class CurrencyViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    pagination_class = None
    serializer_class = CurrencySerializer
    queryset = Currency.objects.all()
    pagination_class = None


class MeasuringUnitViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = MeasuringUnitSerializer
    pagination_class = None
    queryset = MeasuringUnit.objects.all()


class MediaTypeViewset(viewsets.ModelViewSet):
    http_method_names = ["get"]
    serializer_class = MediaTypeSerializer
    pagination_class = None
    queryset = MediaType.objects.all()


class TagViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = TagSerializer
    pagination_class = None
    queryset = Tag.objects.all()

    def get_queryset(self):
        if self.action == "list":
            return OrganizationResourceQuerysetMutator(queryset=self.queryset).get_queryset()
        return super().get_queryset()

    def partial_update(self, request, *args, **kwargs):
        OrganizationResourceValidator(instance_organization_id=self.get_object().organization_id).validate()
        return super().partial_update(request, *args, **kwargs)


class PackageViewset(viewsets.ModelViewSet):
    http_method_names = ["get", "post", "patch", "delete"]
    serializer_class = PackageSerializer
    pagination_class = None
    queryset = Package.objects.all()


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = (
        Organization.objects.all()
        .select_related("country")
        .prefetch_related(
            "organization_packages",
            "organization_packages__package",
        )
        .annotate(
            users_count=Count("organization_users", distinct=True),
            candidates_count=Count("organization_candidates", distinct=True),
        )
    )
    serializer_class = OrganizationSerializer
    http_method_names = ["get", "post", "patch", "delete"]
    filter_backends = [OrganizationFilterBackend]

    def get_serializer_class(self):
        if self.action in ["create", "partial_update"]:
            return OrganizationEditSerializer
        return super().get_serializer_class()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        response = OrganizationSerializer(organization).data
        return Response(response, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        organization = serializer.save()
        organization.refresh_from_db()
        response = OrganizationSerializer(organization).data
        return Response(response, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="assign-organization-user")
    def assign_organization_user(self, request):
        if OrganizationUser.objects.filter(
            user_id=request.data["user"],
        ).exists():
            return make_error_response(data=request.data, message="This user already exists with an organization.")

        serializer = OrganizationUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def remove_organization_user(self, request, *args, **kwargs):
        OrganizationUser.objects.filter(id=self.kwargs["pk"]).update(meta_status="deleted")
        return Response(status=status.HTTP_204_NO_CONTENT)
