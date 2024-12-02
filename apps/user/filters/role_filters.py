import json

from django.db.models import Q
from rest_framework import filters


class RoleFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        name = request.query_params.get("name")
        permissions = request.query_params.get("permissions")

        q_filter = Q()

        if name:
            name = str(name)
            q_filter &= Q(name__icontains=name)

        if permissions:
            permissions = json.loads(permissions)
            permissions = [int(id) for id in permissions]
            q_filter &= Q(role_permissions__permission_id__in=permissions)
            q_filter &= Q(role_permissions__is_active=True)

        return queryset.filter(q_filter).distinct()
