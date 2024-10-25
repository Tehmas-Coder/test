from django.db.models import F

from apps.user.models import Role, UserRole
from utils.rna_utils import remove_extra_underscore_from_key_names


def get_user_role_detail(user_id: int):
    return remove_extra_underscore_from_key_names(list(UserRole.objects.filter(user_id=user_id).annotate(role_name=F("role__name")).values()))[0]


def get_roles_names(role_ids: list[int]) -> list[str]:
    return list(Role.objects.filter(id__in=role_ids).values_list("slug", flat=True))
