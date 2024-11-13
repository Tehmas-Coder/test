from django.contrib.auth.models import AnonymousUser
from django.db.models import F

from apps.organization.models.organization_models import OrganizationUser
from apps.user.models import BaseUser, Role, UserRole
from core.middlewares.current_user_middleware import get_current_user
from core.middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response, remove_extra_underscore_from_key_names


def get_user_role_detail(user_id: int):
    return remove_extra_underscore_from_key_names(list(UserRole.objects.filter(user_id=user_id).annotate(role_name=F("role__name")).values()))[0]


def get_roles_names(role_ids: list[int]) -> list[str]:
    return list(Role.objects.filter(id__in=role_ids).values_list("slug", flat=True))


def get_current_user_organization():
    current_user = get_current_user()
    if isinstance(current_user, AnonymousUser):
        current_user = None
    if current_user is not None:
        current_user_organization = current_user.user_organizations.first()
        if current_user_organization:
            return current_user_organization.organization_id
        else:
            ResponseMiddleware.return_now(make_error_response(message="User doesn't belong to any organization"))
    else:
        ResponseMiddleware.return_now(make_error_response(message="User is not logged in"))
