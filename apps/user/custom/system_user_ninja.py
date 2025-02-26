from rest_framework import status
from rest_framework.response import Response

from apps.organization.models.organization_models import OrganizationUser
from apps.user.models.user_models import BaseUser, Role, UserRole
from apps.user.utils.user_utils import get_current_user_organization
from middlewares.response_middleware import ResponseMiddleware


class SystemUserNinja:
    """
    SystemUserNinja class handles the
    creation of system users in the organization.

    :Attributes:
    - `logged_in_user_organization` (int): The organization ID of the logged-in user.
    - `data_dict` (dict): The dictionary containing the system user data.
    - `roles` (QuerySet): The roles retrieved based on the data.
    - `role_slug_id_hashmap` (dict): The role slug to role ID hashmap.
    - `existing_users_email_and_instance_hashmap` (dict): The email to user instance hashmap.
    - `existing_organization_users_email_and_instance_hashmap` (dict): The email to organization user instance hashmap.
    - `unentertained_emails` (list): The list of unentertained emails.

    :Methods:
    - `create_system_user()`: Creates system users based on the provided data.
    """

    def __init__(self, request_data):
        self.logged_in_user_organization = get_current_user_organization()
        self.data_dict: dict = request_data
        self.roles = None
        self.role_slug_id_hashmap: dict = {}
        self.existing_users_email_and_instance_hashmap: dict = {}
        self.existing_organization_users_email_and_instance_hashmap: dict = {}
        self.unentertained_emails: list = []

    def create_system_user(self):
        self.__collect_roles()
        self.__fetch_users_and_organization_users()
        self.__process_system_users()
        return self.unentertained_emails

    def __collect_roles(self):
        """
        Collects the roles based on the provided data and constructs a role_slug to role_id hashmap.
        """
        role_slugs = [f"{self.logged_in_user_organization}-{one_dict['Slug']}" for one_dict in self.data_dict]
        slugs_to_role_name_hashmap = {f"{self.logged_in_user_organization}-{one_dict['Slug']}": one_dict["RoleName"] for one_dict in self.data_dict}

        self.roles = Role.objects.filter(slug__in=role_slugs, is_system_role=True)
        found_role_slugs = set(self.roles.values_list("slug", flat=True))
        missing_slugs = set(role_slugs) - found_role_slugs

        if missing_slugs:
            missing_role_names = [slugs_to_role_name_hashmap[slug] for slug in missing_slugs]
            ResponseMiddleware.return_now(
                Response(
                    {"status": "failed", "message": f"These roles are not created in QB yet: {', '.join(missing_role_names)}."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            )
        self.role_slug_id_hashmap = {role.slug: role.id for role in self.roles}  # type: ignore

    def __fetch_users_and_organization_users(self):
        emails = [one_user["Email"] for one_user in self.data_dict]

        existing_users = BaseUser.objects.filter(email__in=emails)
        self.existing_users_email_and_instance_hashmap = {user.email: user for user in existing_users}

        organization_users = OrganizationUser.objects.filter(user__email__in=emails).select_related("organization", "user")
        self.existing_organization_users_email_and_instance_hashmap = {org_user.user.email: org_user for org_user in organization_users}

    def __process_system_users(self):
        """
        Processes system users by iterating through the data dictionary and performing the following actions:
        - Constructs a role_slug and retrieves the corresponding role_id.
        - Checks if the user should be deleted.
        - Checks if the user already exists in the system and organization.
        - Creates a new system user if the user does not exist.
        - Deletes the user role if marked for deletion.
        - Creates or updates the user role if not marked for deletion.
        - Creates an organization user if the user does not exist in the organization.
        This function updates the user roles and organization users based on the provided data.
        """
        for one_user in self.data_dict:
            role_slug = f"{self.logged_in_user_organization}-{one_user['Slug']}"
            role_id = self.role_slug_id_hashmap[role_slug]
            email = one_user["Email"]
            to_delete = one_user.get("ToDelete", False)

            user_instance = self.existing_users_email_and_instance_hashmap.get(email)
            create_organization_user = False

            if email in self.existing_organization_users_email_and_instance_hashmap:
                org_user = self.existing_organization_users_email_and_instance_hashmap[email]
                if org_user.organization_id != self.logged_in_user_organization:  # type: ignore
                    self.unentertained_emails.append(email)
                    continue
            else:
                create_organization_user = True

            if not user_instance:
                user_instance = self.__create_system_user(email, role_id, one_user)
            else:
                if to_delete:
                    UserRole.objects.filter(user=user_instance, role_id=role_id).update(meta_status="deleted")
                else:
                    UserRole.objects.get_or_create(user=user_instance, role_id=role_id, defaults={"user": user_instance, "role_id": role_id})

            if create_organization_user:
                OrganizationUser.objects.create(user=user_instance, organization_id=self.logged_in_user_organization)

    def __create_system_user(self, email, role_id, one_user):
        user_instance = BaseUser.objects.create(
            email=email,
            first_name=one_user["FirstName"],
            last_name=one_user["LastName"],
            phone=one_user["PhoneNumber"],
            date_of_birth=one_user["DateOfBirth"],
        )
        UserRole.objects.create(user=user_instance, role_id=role_id)
        self.existing_users_email_and_instance_hashmap[email] = user_instance
        return user_instance
