import django_filters
from django.db import models
from django_filters import rest_framework as filters

from apps.user.models.user_models import BaseUser


class UserFilter(filters.FilterSet):
    min_age = django_filters.NumberFilter(method="filter_by_min_age")
    max_age = django_filters.NumberFilter(method="filter_by_max_age")
    emails = django_filters.CharFilter(method="filter_by_emails")
    search = django_filters.CharFilter(method="filter_by_search")
    meta_status = django_filters.CharFilter(field_name="meta_status")
    is_verified = django_filters.BooleanFilter(field_name="is_verified")

    class Meta:
        model = BaseUser
        fields = [
            "emails",
            "is_active",
            "is_superuser",
            "min_age",
            "max_age",
            "search",
            "meta_status",
            "is_verified",
        ]

    def filter_by_min_age(self, queryset, name, value):
        from datetime import date, timedelta

        min_birthdate = date.today() - timedelta(days=int(value) * 365.25)
        return queryset.filter(date_of_birth__lte=min_birthdate)

    def filter_by_max_age(self, queryset, name, value):
        from datetime import date, timedelta

        max_birthdate = date.today() - timedelta(days=int(value) * 365.25)
        return queryset.filter(date_of_birth__gte=max_birthdate)

    def filter_by_emails(self, queryset, name, value):
        email_list = value.split(",")
        return queryset.filter(email__in=email_list)

    def filter_by_search(self, queryset, name, value):
        return queryset.filter(models.Q(first_name__icontains=value) | models.Q(last_name__icontains=value) | models.Q(email__icontains=value))
