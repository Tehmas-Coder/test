from apps.user.models import Permission, Role


class RoleNinja:
    def __init__(self) -> None:
        pass

    @staticmethod
    def add_role_permissions(user_id) -> Role:
        """
        Add all permissions to a role with is_active set to False
        """
        permission_ids_list = list(Permission.objects.all().values_list("id", flat=True))
        new_role_instance = Role.objects.prefetch_related("permissions").get(pk=user_id)
        if len(permission_ids_list):
            new_role_instance.permissions.set(permission_ids_list)
        return new_role_instance
