from apps.user.models.user_models import Permission, Role
from middlewares.current_user_middleware import get_current_user


class RoleNinja:
    def __init__(self) -> None:
        pass

    @staticmethod
    def add_role_permissions(user_id) -> Role:
        """
        Add permissions to the role based on the user's superuser status.

        Args:
            user_id (int): The ID of the user.

        Returns:
            Role: The updated role instance.
        """
        if get_current_user().is_superuser:  # type: ignore
            permission_ids_list = list(Permission.objects.all().values_list("id", flat=True))
        else:
            permission_ids_list = list(Permission.objects.exclude(context_value__in=["studentapply", "candidates"]).values_list("id", flat=True))
        new_role_instance = Role.objects.prefetch_related("permissions").get(pk=user_id)
        if len(permission_ids_list):
            new_role_instance.permissions.set(permission_ids_list)
        return new_role_instance
