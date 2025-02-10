import json

from django.db.models import Q
from rest_framework import filters


class QuestionFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):
        subjects = request.query_params.get("subjects")
        education_levels = request.query_params.get("education_levels")
        types = request.query_params.get("types")
        tags = request.query_params.get("tags")
        difficulty_levels = request.query_params.get("difficulty_levels")
        countries = request.query_params.get("countries")
        is_optional = request.query_params.get("is_optional")
        subject_education_levels = request.query_params.get("subject_education_levels")
        title = request.query_params.get("title")
        organizations = request.query_params.get("organizations")

        q_filter = Q()

        if organizations:
            organizations = json.loads(organizations)
            organizations = [int(id) for id in organizations]
            q_filter &= Q(Q(organization_id__in=organizations) | Q(organization_id__isnull=True))

        if subjects:
            subjects = json.loads(subjects)
            subjects = [int(id) for id in subjects]
            q_filter &= Q(subjects__subject_education_level__subject_id__in=subjects)

        if education_levels:
            education_levels = json.loads(education_levels)
            education_levels = [int(id) for id in education_levels]
            q_filter &= Q(subjects__subject_education_level__education_level_id__in=education_levels)

        if subject_education_levels:
            subject_education_levels = json.loads(subject_education_levels)
            subject_education_levels = [int(id) for id in subject_education_levels]
            q_filter &= Q(subjects__subject_education_level_id__in=subject_education_levels)

        if types:
            types = json.loads(types)
            types = [int(id) for id in types]
            q_filter &= Q(type_id__in=types)

        if tags:
            tags = json.loads(tags)
            tags = [int(id) for id in tags]
            q_filter &= Q(tags__in=tags)

        if difficulty_levels:
            difficulty_levels = json.loads(difficulty_levels)
            difficulty_levels = [int(id) for id in difficulty_levels]
            q_filter &= Q(subjects__difficulty_level_id__in=difficulty_levels)

        if countries:
            countries = json.loads(countries)
            countries = [int(id) for id in countries]
            q_filter &= Q(subjects__countries__in=countries)

        if is_optional:
            is_optional = int(is_optional)
            q_filter &= Q(subjects__is_optional=is_optional)

        if title:
            title = str(title)
            q_filter &= Q(title__icontains=title)

        # ? Here i have removed .distinct() from the below queryset as it gets unique questions but we want if a question exist multiple times it must be in different subjects or in same subject but from different education level
        return queryset.filter(q_filter).distinct()
