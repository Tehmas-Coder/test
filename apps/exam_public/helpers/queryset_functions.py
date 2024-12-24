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
