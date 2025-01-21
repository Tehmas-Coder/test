import json

from django.db.models import Q
from rest_framework import filters

from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user


class CandidateExamFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        user = request.query_params.get("user")
        search = request.query_params.get("search")
        countries = request.query_params.get("countries")
        is_marking = request.query_params.get("is_marking")
        statuses = request.query_params.get("statuses")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")
        education_levels = request.query_params.get("education_levels")
        exam = request.query_params.get("exam")

        q_filter = Q()

        if get_current_user() and ("candidate" not in get_current_user().get_user_role_slugs):  # type: ignore
            is_superuser = get_current_user().is_superuser  # type: ignore
            organization = None if is_superuser else get_current_user_organization()
            q_filter &= Q(organization_id=organization)

        if user:
            user = int(user)
            q_filter &= Q(candidate__user_id=user)

        if search:
            search = str(search)
            q_filter &= Q(
                Q(candidate__user__first_name__icontains=search)
                | Q(candidate__user__last_name__icontains=search)
                | Q(candidate__user__email__icontains=search)
                | Q(candidate_email__icontains=search)
            )

        if countries:
            countries = json.loads(countries)
            countries = [int(id) for id in countries]
            q_filter &= Q(candidate__user__country_id__in=countries)

        if is_marking:
            is_marking = bool(is_marking)
            if is_marking:
                q_filter &= ~Q(exam_status__in=["assigned", "expired"])

        if statuses:
            statuses = json.loads(statuses)
            statuses = [str(status) for status in statuses]
            q_filter &= Q(exam_status__in=statuses)

        if start_date and not end_date:
            start_date = str(start_date)
            q_filter &= Q(start_datetime__date=start_date)

        if end_date and not start_date:
            end_date = str(end_date)
            q_filter &= Q(end_datetime__date=end_date)

        if start_date and end_date:
            start_date = str(start_date)
            end_date = str(end_date)
            q_filter &= Q(start_datetime__date__range=[start_date, end_date])

        if education_levels:
            education_levels = json.loads(education_levels)
            education_levels = [int(level) for level in education_levels]
            q_filter &= Q(exam_backlog__education_level__in=education_levels)

        if exam:
            exam = str(exam)
            q_filter &= Q(exam_backlog__name__icontains=exam)

        return queryset.filter(q_filter).distinct()
