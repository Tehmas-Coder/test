from django.db.models import Prefetch, QuerySet

from apps.organization.models.organization_models import (
    OrganizationPackage,
    OrganizationUser,
)
from apps.user.models.user_models import BaseUser


def get_organization_detailed_queryset(
    model, country=False, organization_users=False, organization_candidates=False, organization_packages=False
) -> QuerySet:
    organization_queryset = model.objects.all()

    if country:
        organization_queryset = organization_queryset.select_related("country")

    if organization_packages:
        organization_queryset = organization_queryset.prefetch_related(
            Prefetch("organization_packages", queryset=OrganizationPackage.objects.all().select_related("package"))
        )

    if organization_users:
        organization_queryset = organization_queryset.prefetch_related(
            Prefetch(
                "organization_users",
                OrganizationUser.objects.all()
                .prefetch_related(
                    Prefetch("user", BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True))
                )
                .distinct(),
            )
        )

    if organization_candidates:
        from apps.exam_public.models.exam_public_models import Candidate

        organization_queryset = organization_queryset.prefetch_related(
            Prefetch(
                "organization_candidates",
                Candidate.objects.all().prefetch_related(
                    Prefetch("user", BaseUser.get_detail_queryset(country=True, roles=True, role_permissions=True, role_permissions_permission=True))
                ),
            )
        )

    return organization_queryset
