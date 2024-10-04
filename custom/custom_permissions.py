import re

from django.forms.models import model_to_dict
from rest_framework.permissions import BasePermission

from apps.user.models import Resource


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

        user_role = request_user.roles.all().values().first()
        role_id = user_role["id"]

        # TODO: Here only the resources assigned to the system role will be allowed, later when role_resource seeds will be added
        if user_role["name"].lower() == "system":
            return True

        # return True
        return validate_resources(request_method, request_path, role_id)


def is_url_public(request_method, request_path):
    bypassed_api_urls_dict = {
        "get": [
            "/countries/",
            "/timezones/",
            "/regions/",
            "/states/",
            "/languages/",
            "/currencies/",
            "/measuring-units/",
            "/media-types/",
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


def validate_resources(request_method, request_path, role_id):
    regex_pattern = string_url_to_regex(request_path)
    resource_id = 0

    try:
        resource_dict = model_to_dict(Resource.objects.get(regex__exact=regex_pattern, method=request_method))
        resource_id = resource_dict["id"]
    except:
        print(f"No Resource ({request_method} => {request_path}) found on server.")
        return False

    # try:
    #     RoleResource.objects.get(role_id=role_id, resource_id=resource_id)
    # except:
    #     print(f"RoleID ({role_id}) id un-authorized for ({request_method} => {request_path}) request.")
    #     return False

    return True


def string_url_to_regex(string_url):
    exam_url = "/candidate-exam/token="
    if string_url.startswith(exam_url):
        return "^/candidate-exam/[0-9]+/$"

    # Escape special characters in the input string
    escaped_string = re.escape(string_url)

    # Replace the placeholder for the number with the regex notation [0-9]+
    regex_pattern = re.sub(r"\/[0-9]+\/", r"\/[0-9]+\/", escaped_string)

    # Add anchors to match the start and end of the string
    regex_pattern = f"^{regex_pattern}$"
    regex_pattern = regex_pattern.replace("\\", "")

    return regex_pattern
