from django.db.models import Q
from rest_framework.generics import QuerySet

from apps.organization.models.organization_models import OrganizationPackage
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


class VisibilitySetter:
    """
    This class is used to set the visibility of the resource to public or non public based on the user's superuser status.
    """

    def set_visibility(self, request_data: dict) -> dict:
        if get_current_user().is_superuser:  # type: ignore
            request_data["is_public"] = 1
        else:
            request_data["is_public"] = 0
        return request_data


class OrganizationValidator:
    def __init__(self, organization_id=None) -> None:
        if (organization_id is None) and (not get_current_user().is_superuser):  # type: ignore
            organization_id = get_current_user_organization()
        self.organization_id = organization_id

    def validate(self) -> bool:
        return True


class OrganizationResourceValidator(OrganizationValidator):
    """
    This class is used to validate the organization_id of the resource, to check if the resource belongs to the organization of the user.
    """

    def __init__(self, organization_id=None, instance_organization_id=None) -> None:
        super().__init__(organization_id)
        self.instance_organization_id = instance_organization_id

    def validate(self) -> bool:
        if (not get_current_user().is_superuser) and (self.instance_organization_id != self.organization_id):  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="Failed: This resource doesn't belong to your organization"))
        return True


class OrganizationResourceQuerysetMutator:
    """
    This class is used to filter the queryset based on the organization_id.
    """

    def __init__(self, organization_id=None, queryset=None, is_public=False) -> None:
        if (organization_id is None) and (not get_current_user().is_superuser):  # type: ignore
            organization_id = get_current_user_organization()
        self.organization_id = organization_id
        self.queryset = queryset
        self.is_public = is_public

    def get_queryset(self) -> QuerySet:
        q_filter = Q()
        if not get_current_user().is_superuser:  # type: ignore
            if self.is_public:
                q_filter &= Q(organization_id=self.organization_id) | Q(is_public=True)
            else:
                q_filter &= Q(organization_id=self.organization_id) | Q(organization_id=None)
        return self.queryset.filter(q_filter)  # type: ignore


class OrganizationPackageLimitValidator(OrganizationValidator):
    """
    This class is used to validate the package limits of the organization.
    """

    def __init__(self, organization_id=None) -> None:
        super().__init__(organization_id)
        self.organization_package = OrganizationPackage.objects.filter(organization_id=self.organization_id).select_related("package").last()

    def validate(self) -> bool:
        return super().validate()

    def validate_limit(self, current_count, total_limit) -> int:
        if not (current_count <= total_limit):
            raise ValueError("Package limit for this action has been reached")
        current_count += 1
        return current_count

    def save_organization_package(self) -> None:
        self.organization_package.save()  # type: ignore
