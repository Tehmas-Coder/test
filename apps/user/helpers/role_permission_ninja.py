from django.db.models import Q
from django.utils.text import slugify

from apps.user.models import Permission, Role, RolePermission
from apps.user.utils.utils import get_current_user_organization
from core.middlewares.current_user_middleware import get_current_user
from core.middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


class RolePermissionNinja:
    def __init__(self, request_data: dict) -> None:
        self.data_dict = request_data

    # ---------------------------------------------------------------------------- #
    #                               PUBLIC METHODS                                 #
    # ---------------------------------------------------------------------------- #

    def update_role_permissions(self):
        requested_user_organization_id = get_current_user_organization()
        requested_role_name = self.data_dict["RoleName"]
        requested_role_name_slug = slugify(f"{requested_user_organization_id}-{requested_role_name}")
        role_instance = Role.objects.filter(slug=requested_role_name_slug).first()

        if len(self.data_dict.get("default_qb_permissions", [])):
            if role_instance:
                self.__deactivate_all_permissions_for_existing_student_apply_role(role_instance)
            else:
                role_instance = self.__create_new_student_apply_role(requested_role_name, requested_user_organization_id)

            self.__activate_new_role_permissions(role_instance)
        else:
            self.__activate_existing_role_permissions(role_instance)

    def delete_role_with_its_permissions(self):
        requested_user_role_slugs = get_current_user().get_user_role_slugs  # type: ignore
        requested_role_name = self.data_dict.get("role")
        if not "system" in requested_user_role_slugs:
            ResponseMiddleware.return_now(make_error_response())
        requested_role_slug = slugify(f"{get_current_user_organization()}-{requested_role_name}")
        role_instance = Role.objects.filter(slug=requested_role_slug).first()
        if not role_instance:
            ResponseMiddleware.return_now(make_error_response(message="Role not found"))
        role_permissions = RolePermission.objects.filter(role=role_instance)
        role_permissions.update(meta_status="deleted")
        role_instance.delete()  # type: ignore

    # ---------------------------------------------------------------------------- #
    #                               PRIVATE METHODS                                #
    # ---------------------------------------------------------------------------- #

    def __deactivate_all_permissions_for_existing_student_apply_role(self, role_instance):
        role_instance.is_system_role = True  # type: ignore
        role_instance.save()
        RolePermission.objects.filter(role=role_instance).update(is_active=False)

    def __create_new_student_apply_role(self, requested_role_name, requested_user_organization_id):
        role_instance = Role.objects.create(name=requested_role_name, is_system_role=True, organization_id=requested_user_organization_id)
        permission_ids_list = list(
            Permission.objects.exclude(Q(context_value="studentapply") & ~Q(name__icontains="Login From Student Apply"))
            .exclude(context_value="candidates")
            .values_list("id", flat=True)
        )
        role_instance.permissions.set(permission_ids_list)
        return role_instance

    def __activate_new_role_permissions(self, role_instance):
        request_permission_ids_list = [one_dict["id"] for one_dict in self.data_dict["default_qb_permissions"]]
        RolePermission.objects.filter(
            Q(role=role_instance) & (Q(permission_id__in=request_permission_ids_list) | Q(permission__name__icontains="Login From Student Apply"))
        ).update(is_active=True)

    def __activate_existing_role_permissions(self, role_instance):
        RolePermission.objects.bulk_update(
            [
                RolePermission(id=one_permission["id"], role=role_instance, is_active=one_permission["is_active"])
                for one_permission in self.data_dict["qb_role_permissions"]
            ],
            fields=["is_active"],
        )
