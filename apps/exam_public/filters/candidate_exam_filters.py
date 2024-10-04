import json

from django.db.models import Q
from rest_framework import filters


class CandidateExamFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        user = request.query_params.get("user")
        search = request.query_params.get("search")
        countries = request.query_params.get("countries")

        q_filter = Q()

        if user:
            user = int(user)
            q_filter &= Q(candidate__user_id=user)

        if search:
            search = str(search)
            q_filter &= Q(
                Q(candidate__user__first_name__icontains=search)
                | Q(candidate__user__last_name__icontains=search)
                | Q(candidate__user__email__icontains=search)
            )

        if countries:
            countries = json.loads(countries)
            countries = [str(name) for name in countries]
            q_filter &= Q(candidate__user__country__name__in=countries)

        return queryset.filter(q_filter).distinct()
