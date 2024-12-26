from django.db.models import Prefetch, QuerySet


def get_candidate_detailed_queryset(model, organization=False, user=False) -> QuerySet:
    candidate_queryset = model.objects.get_queryset()
    if organization:
        candidate_queryset = candidate_queryset.select_related("organization", "organization__country")
    if user:
        from apps.user.models.user_models import BaseUser

        candidate_queryset = candidate_queryset.prefetch_related(
            Prefetch("user", queryset=BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True))
        )
    return candidate_queryset


def get_candidate_exam_detailed_queryset(model, exam_backlog=False, schedule=False, candidate=False) -> QuerySet:
    from apps.exam_public.models.exam_public_models import Candidate

    candidate_exam_queryset = model.objects.get_queryset()
    if exam_backlog:
        candidate_exam_queryset = candidate_exam_queryset.select_related("exam_backlog")
    if schedule:
        candidate_exam_queryset = candidate_exam_queryset.select_related("schedule")
    if candidate:
        candidate_exam_queryset = candidate_exam_queryset.prefetch_related(
            Prefetch("candidate", queryset=Candidate.get_detail_queryset(organization=True, user=True))
        )
    return candidate_exam_queryset
