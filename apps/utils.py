from django.db.models import F

from apps.user.models import Role, UserRole
from utils.rna_utils import remove_extra_underscore_from_key_names


def get_user_role_detail(user_id: int):
    return remove_extra_underscore_from_key_names(list(UserRole.objects.filter(user_id=user_id).annotate(role_name=F("role__name")).values()))[0]


def get_role_name(role_id: int):
    return Role.objects.get(id=role_id).name
