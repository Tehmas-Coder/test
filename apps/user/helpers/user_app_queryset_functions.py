from django.db.models import Prefetch


def get_user_detailed_queryset(model, country=False, roles=False, role_permissions=False, role_permissions_permission=False):
    user_queryset = model.objects.all().select_related("profile_picture")
    if country:
        user_queryset = user_queryset.select_related("country")
    if roles:
        from apps.user.models import Role

        role_queryset = Role.objects.all()
        if role_permissions:
            from apps.user.models import RolePermission

            role_permissions_queryset = RolePermission.objects.all()
            if role_permissions_permission:
                role_permissions_queryset = role_permissions_queryset.select_related("permission")

            role_queryset = role_queryset.prefetch_related(Prefetch("role_permissions", role_permissions_queryset))

        user_queryset = user_queryset.prefetch_related(Prefetch("roles", role_queryset))
    return user_queryset
