from threading import local

from django.contrib.auth.models import AnonymousUser
from django.db.models import F

from apps.user.models.user_models import Role, UserRole
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response, remove_extra_underscore_from_key_names

_user_organization = local()


def get_roles_names(role_ids: list[int]) -> list[str]:
    """
    Retrieve the role names based on the role IDs.

    Args:
        role_ids (list[int]): A list of role IDs.

    Returns:
        list[str]: A list of role names
    """
    return list(Role.objects.filter(id__in=role_ids).values_list("slug", flat=True))


def get_current_user_organization():
    """
    Retrieve the organization of the current user.

    Returns:
        int: The organization ID of the current user.
    """
    current_user = get_current_user()
    if isinstance(current_user, AnonymousUser):
        current_user = None
    if current_user:
        user_organization = getattr(_user_organization, "value", None)
        if not user_organization:
            organization_user_or_candidate_user_instance = current_user.user_organizations.first() or current_user.user_candidates.first()
            if organization_user_or_candidate_user_instance:
                _user_organization.value = organization_user_or_candidate_user_instance.organization_id
                user_organization = getattr(_user_organization, "value", None)
            else:
                ResponseMiddleware.return_now(make_error_response(message="User doesn't belong to any organization"))
        return user_organization
    else:
        ResponseMiddleware.return_now(make_error_response(message="User is not logged in"))


def get_current_user_candidates():
    current_user = get_current_user()
    if isinstance(current_user, AnonymousUser):
        current_user = None
    if current_user:
        return list(current_user.user_candidates.all())
    else:
        ResponseMiddleware.return_now(make_error_response(message="User is not logged in"))
