import json

from django.db.models import Q
from rest_framework import filters


class OrganizationFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        name = request.query_params.get("name")
        country = request.query_params.get("country")
        packages = request.query_params.get("packages")

        q_filter = Q()

        if name:
            name = str(name)
            q_filter &= Q(name__icontains=name)

        if country:
            country = str(country)
            q_filter &= Q(country__name__icontains=country)

        if packages:
            packages = json.loads(packages)
            packages = [int(id) for id in packages]
            q_filter &= Q(organization_packages__package_id__in=packages)

        return queryset.filter(q_filter).distinct()
