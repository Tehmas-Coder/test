from abc import ABC, abstractmethod

from django.db.models import Q
from rest_framework.generics import QuerySet

from apps.organization.models.organization_models import OrganizationPackage
from apps.user.utils.user_utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


class VisibilitySetter:
    """
    This class is used to set the visibility of the resource to public or non public based on the user's superuser status.
    """

    def set_visibility(self, request_data: dict) -> dict:
        """
        Set the visibility of the resource to public or non public based on the user's superuser status.

        Args:
            request_data (dict): The request data.

        Returns:
            dict: The updated request data.
        """
        if get_current_user().is_superuser:  # type: ignore
            request_data["is_public"] = 1
        else:
            request_data["is_public"] = 0
        return request_data


class OrganizationValidator(ABC):
    """
    Abstract base class for organization validators.

    :Attributes:
    - `organization_id` (int): The organization id.

    :Methods:
    - `validate()`: Validates the organization
    """

    def __init__(self, organization_id: int | None = None) -> None:
        if (organization_id is None) and (not get_current_user().is_superuser):  # type: ignore
            organization_id = get_current_user_organization()
        self.organization_id = organization_id

    @abstractmethod
    def validate(self) -> bool:
        pass


class OrganizationResourceValidator(OrganizationValidator):
    """
    This class is used to validate the organization_id of the resource, to check if the resource belongs to the organization of the user.

    :Attributes:
    - `instance_organization_id` (int): The organization id of the resource.

    :Methods:
    - `validate()`: Validates the organization id of the resource.

    :Raises:
    - ResponseMiddleware: If the resource doesn't belong to the user's organization

    :Returns:
    - bool: True if the resource belongs to the user's organization, False otherwise.
    """

    def __init__(self, organization_id: int | None = None, instance_organization_id: int | None = None) -> None:
        super().__init__(organization_id)
        self.instance_organization_id = instance_organization_id

    def validate(self) -> bool:
        if (not get_current_user().is_superuser) and (self.instance_organization_id != self.organization_id):  # type: ignore
            ResponseMiddleware.return_now(make_error_response(message="Failed: This resource doesn't belong to your organization"))
        return True


class OrganizationPackageLimitValidator(OrganizationValidator):
    """
    This class is used to validate the package limits of the organization.

    :Attributes:
    - `organization_package` (OrganizationPackage): The organization package.

    :Methods:
    - `validate_limit(current_count, total_limit)`: Validates the limit of the organization package.
    - `save_organization_package()`: Saves the organization package.

    :Raises:
    - ValueError: If the resource count exceeds the organization package limits.
    """

    def __init__(self, organization_id: int | None = None) -> None:
        super().__init__(organization_id)
        self.organization_package = OrganizationPackage.objects.filter(organization_id=self.organization_id).select_related("package").last()

    def validate(self) -> bool:
        return super().validate()

    def validate_limit(self, current_count: int, total_limit: int) -> int:
        if not (current_count < total_limit):
            raise ValueError("Your Organizational Package limit for this action has been reached")
        current_count += 1
        return current_count

    def save_organization_package(self) -> None:
        self.organization_package.save()  # type: ignore


class OrganizationResourceQuerysetMutator:
    """
    This class is used to mutate the queryset based on the user's superuser status.

    If the user is a superuser, the queryset is returned as is.

    If the user is not a superuser, the queryset is filtered based on the organization_id and the resource's is_public status.

    :Attributes:
    - `organization_id` (int): The organization id.
    - `queryset` (QuerySet): The queryset to be mutated.
    - `is_public` (bool): True if the resource is public, False otherwise.

    :Methods:
    - `get_queryset()`: Returns the mutated queryset.
    """

    def __init__(self, organization_id: int | None = None, queryset=None, is_public=False) -> None:
        if (organization_id is None) and get_current_user() and (not get_current_user().is_superuser):  # type: ignore
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
                q_filter &= Q(organization_id=self.organization_id) | Q(organization__isnull=True)
        return self.queryset.filter(q_filter)  # type: ignore
