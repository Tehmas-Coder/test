import json

from django.db.models import Q
from rest_framework import filters


class CandidateFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        organizations = request.query_params.get("organizations")

        q_filter = Q()

        if organizations:
            organizations = json.loads(organizations)
            organizations = [int(id) for id in organizations]
            q_filter &= Q(organization_id__in=organizations)

        return queryset.filter(q_filter).distinct()
