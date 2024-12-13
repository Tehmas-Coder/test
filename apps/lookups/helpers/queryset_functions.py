from django.db.models import Prefetch, QuerySet

from apps.organization.models.organization_models import OrganizationUser


def get_organization_detailed_queryset(model, country=False, organization_users=False, organization_candidates=False) -> QuerySet:
    organization_queryset = model.objects.all()

    if country:
        organization_queryset = organization_queryset.select_related("country")

    if organization_users:
        organization_queryset = organization_queryset.prefetch_related(
            Prefetch(
                "organization_users",
                OrganizationUser.objects.all()
                .select_related(
                    "user",
                    "user__country",
                    "user__profile_picture",
                )
                .prefetch_related(
                    "user__roles",
                    "user__roles__role_permissions",
                    "user__roles__role_permissions__permission",
                ),
            )
        )

    if organization_candidates:
        from apps.exam_public.models.exam_public_models import Candidate

        organization_queryset = organization_queryset.prefetch_related(
            Prefetch(
                "organization_candidates",
                Candidate.objects.all()
                .select_related(
                    "user",
                    "user__country",
                    "user__profile_picture",
                )
                .prefetch_related(
                    "user__roles",
                    "user__roles__role_permissions",
                    "user__roles__role_permissions__permission",
                ),
            )
        )

    return organization_queryset
