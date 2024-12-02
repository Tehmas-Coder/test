import json

from django.db.models import Q
from rest_framework import filters


class ExamFilterBackend(filters.BaseFilterBackend):
    def filter_queryset(self, request, queryset, view):

        name = request.query_params.get("name")
        exam_status = request.query_params.get("exam_status")
        education_levels = request.query_params.get("education_levels")
        subject_education_levels = request.query_params.get("subject_education_levels")

        q_filter = Q()

        if name:
            name = str(name)
            q_filter &= Q(name__icontains=name)

        if exam_status:
            exam_status = str(exam_status)
            q_filter &= Q(exam_status=exam_status)

        if education_levels:
            education_levels = json.loads(education_levels)
            education_levels = [int(id) for id in education_levels]
            q_filter &= Q(education_level_id__in=education_levels)

        if subject_education_levels:
            subject_education_levels = json.loads(subject_education_levels)
            subject_education_levels = [int(id) for id in subject_education_levels]
            q_filter &= Q(examsubject__subject_education_level__in=subject_education_levels)

        return queryset.filter(q_filter).distinct()
