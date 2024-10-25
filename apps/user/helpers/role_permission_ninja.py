from django.utils.text import slugify

from apps.user.models import Role


class RolePermissionNinja:
    def __init__(self, request_data: dict) -> None:
        self.data_dict = request_data

    def update_role_permissions(self):
        requested_role_name = self.data_dict["RoleName"]
        requested_role_name_slug = slugify(requested_role_name)
        role_instance = Role.objects.filter(slug=requested_role_name_slug, name=requested_role_name).first()

        if len(self.data_dict.get("default_qb_permissions", [])):
            self.__create_new_student_apply_role(role_instance)

    def __create_new_student_apply_role(self, role_instance):
        pass
        # if role_instance is not None:
        #     role_instance.is_system_role = True  # type: ignore
