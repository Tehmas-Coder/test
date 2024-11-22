from django.db.models import Prefetch


def get_user_detailed_queryset(model, country=False, roles=False, role_permissions=False, role_permissions_permission=False):
    user_queryset = model.objects.get_queryset().select_related("profile_picture")
    if country:
        user_queryset = user_queryset.select_related("country")
    if roles:
        from apps.user.models.user_models import Role

        role_queryset = get_role_detailed_queryset(Role, True, False, role_permissions, role_permissions_permission)
        user_queryset = user_queryset.prefetch_related(Prefetch("roles", role_queryset))
    return user_queryset


def get_role_detailed_queryset(model, organization=False, permissions=False, role_permissions=False, role_permissions_permission=False):
    role_queryset = model.objects.get_queryset()
    if organization:
        role_queryset = role_queryset.select_related("organization", "organization__country")
    if permissions:
        role_queryset = role_queryset.prefetch_related("permissions")
    if role_permissions:
        from apps.user.models.user_models import RolePermission

        role_permissions_queryset = RolePermission.objects.all()
        if role_permissions_permission:
            role_permissions_queryset = role_permissions_queryset.select_related("permission")

        role_queryset = role_queryset.prefetch_related(Prefetch("role_permissions", role_permissions_queryset))
    return role_queryset
