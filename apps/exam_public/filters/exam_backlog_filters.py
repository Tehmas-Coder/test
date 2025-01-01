import json

from django.db.models import Q


def get_exambacklog_q_filter(request):
    name = request.query_params.get("name")
    education_levels = request.query_params.get("education_levels")
    start_date = request.query_params.get("start_date")
    end_date = request.query_params.get("end_date")

    q_filter = Q()

    if name:
        name = str(name)
        q_filter &= Q(name__icontains=name)

    if education_levels:
        education_levels = json.loads(education_levels)
        education_levels = [int(id) for id in education_levels]
        q_filter &= Q(education_level_id__in=education_levels)

    if start_date and not end_date:
        start_date = str(start_date)
        q_filter &= Q(candidate_exam_examsbacklog__start_datetime__date=start_date)

    if end_date and not start_date:
        end_date = str(end_date)
        q_filter &= Q(candidate_exam_examsbacklog__end_datetime__date=end_date)

    if start_date and end_date:
        start_date = str(start_date)
        end_date = str(end_date)
        q_filter &= Q(candidate_exam_examsbacklog__start_datetime__date__range=[start_date, end_date])

    return q_filter
