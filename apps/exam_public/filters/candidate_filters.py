from django.db.models import Q
from rest_framework import filters

from apps.organization.models.organization_models import OrganizationUser


class CandidateFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        q_filter = Q()

        logged_in_user = request.user
        # TODO: Only show candidates with no organization to superuser on exam assignment
        if not logged_in_user.is_superuser:
            q_filter &= Q(organization_id=OrganizationUser.objects.get(user=logged_in_user).organization_id)  # type:ignore
        return queryset.filter(q_filter).distinct()
