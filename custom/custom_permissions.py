import re

from django.forms.models import model_to_dict
from rest_framework.permissions import BasePermission

from apps.user.models import Resource, RolePermission
from utils.rna_utils import color_print


class IsAuthenticated(BasePermission):
    def has_permission(self, request, view):
        request_user = request.user
        request_method = request.method.lower()
        request_path = request.path.replace("/api", "")

        if is_url_public(request_method, request_path):
            return True

        if not request_user.is_authenticated:
            return False

        if request_user.is_superuser:
            return True

        user_roles = request_user.roles.all()
        user_role_ids = [one_role.id for one_role in user_roles]
        user_roles_names = [one_role.slug for one_role in user_roles]

        # TODO: Here only the resources assigned to the system role will be allowed, later when role_resource seeds will be added
        if "system" in user_roles_names:
            return True

        # return True
        return validate_resources(request_method, request_path, user_role_ids)


def is_url_public(request_method, request_path):
    bypassed_api_urls_dict = {
        "get": [
            "/ping/",
            "/countries/",
            "/timezones/",
            "/regions/",
            "/states/",
            "/languages/",
            "/currencies/",
            "/measuring-units/",
            "/media-types/",
            "/question-types/",
            "/difficulty-levels/",
            # TODO: tags also have permissions, but they are public, check back to remove these from here
            "/tags/",
            # "/countries/(?P<pk>[0-9]+)/",
        ]
    }
    if request_method in bypassed_api_urls_dict:
        for pattern in bypassed_api_urls_dict[request_method]:
            # If the request path matches any pattern, return True
            if re.match(pattern, request_path):
                return True

    return False


def validate_resources(request_method, request_path, role_ids):
    regex_pattern = string_url_to_regex(request_path)

    try:
        resource_dict = model_to_dict(Resource.objects.get(regex__exact=regex_pattern, method=request_method))
        resource_permission = resource_dict["permission"]
    except:
        print(f"No Resource ({request_method} => {request_path}) found on server.")
        return False

    try:
        RolePermission.objects.get(role_id__in=role_ids, permission=resource_permission, is_active=True)

    except:
        color_print("****************************************************************", "red")
        color_print(f"RoleIDs ({role_ids}) are un-authorized for ({request_method} => {request_path}) request.", "red")
        color_print("****************************************************************", "red")
        return False

    # ? This implementation is obsolete and was for the previous implementation of role_resource, use the above implementation
    # try:
    #     RoleResource.objects.get(role_id__in=role_ids, resource_id=resource_id)
    # except:
    #     print(f"RoleIDs ({role_ids}) id un-authorized for ({request_method} => {request_path}) request.")
    #     return False

    color_print("PASSSSSSSSSSSSSSSSS")
    return True


def string_url_to_regex(string_url):
    bypass_url = string_url.split("/token=")
    if len(bypass_url) > 1:
        return f"^{bypass_url[0]}/[0-9]+/$"

    # Escape special characters in the input string
    escaped_string = re.escape(string_url)

    # Replace the placeholder for the number with the regex notation [0-9]+
    regex_pattern = re.sub(r"\/[0-9]+\/", r"\/[0-9]+\/", escaped_string)

    # Add anchors to match the start and end of the string
    regex_pattern = f"^{regex_pattern}$"
    regex_pattern = regex_pattern.replace("\\", "")

    return regex_pattern
