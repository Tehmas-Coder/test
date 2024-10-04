import json

from django.db.models import Q
from rest_framework import filters


class UserFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        name = request.query_params.get("name")
        email = request.query_params.get("email")
        min_age = request.query_params.get("min_age")
        max_age = request.query_params.get("max_age")
        roles = request.query_params.get("roles")
        countries = request.query_params.get("countries")

        q_filter = Q()

        if name:
            name = str(name)
            name = name.split(" ")
            q_filter &= Q(first_name__icontains=name[0]) | Q(last_name__icontains=name[1])

        if email:
            email = str(email)
            q_filter &= Q(email__icontains=email)

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
            countries = [str(name) for name in countries]
            q_filter &= Q(country__name__in=countries)

        return queryset.filter(q_filter).distinct()
