import json

from django.db.models import Q
from rest_framework import filters


class UserFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        search = request.query_params.get("search")
        min_age = request.query_params.get("min_age")
        max_age = request.query_params.get("max_age")
        roles = request.query_params.get("roles")
        countries = request.query_params.get("countries")

        q_filter = Q()

        if search:
            search = str(search)
            q_filter &= Q(Q(first_name__icontains=search) | Q(last_name__icontains=search) | Q(email__icontains=search))

        if min_age:
            from datetime import date, timedelta

            min_birthdate = date.today() - timedelta(days=int(min_age) * 365.25)
            q_filter &= Q(date_of_birth__lte=min_birthdate)

        if max_age:
            from datetime import date, timedelta

            max_birthdate = date.today() - timedelta(days=int(max_age) * 365.25)
            q_filter &= Q(date_of_birth__gte=max_birthdate)

        if roles:
            roles = json.loads(roles)
            roles = [int(id) for id in roles]
            q_filter &= Q(roles__id__in=roles)

        if countries:
            countries = json.loads(countries)
            countries = [int(id) for id in countries]
            q_filter &= Q(country_id__in=countries)

        return queryset.filter(q_filter).distinct().order_by("-id")
