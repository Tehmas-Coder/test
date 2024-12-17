from rest_framework import status
from rest_framework.response import Response

from apps.exam_admin.serializers.exam_serializers import ExamSerializer
from apps.lookups.custom.lookups_classes import (
    OrganizationPackageLimitValidator,
    OrganizationValidator,
    VisibilitySetter,
)
from apps.user.utils.utils import get_current_user_organization
from middlewares.current_user_middleware import get_current_user
from middlewares.response_middleware import ResponseMiddleware
from utils.rna_utils import make_error_response


class ExamVisibilitySetter(VisibilitySetter):
    """
    This class is used to set the visibility of the exam to public or non public based on the user's superuser status.
    """

    def set_visibility(self, request_data: dict) -> dict:
        return super().set_visibility(request_data)


class OrganizationPackageExamLimitValidator(OrganizationPackageLimitValidator):
    """
    This class is used to validate the package limits of the organization for the exam.
    """

    def __init__(self, organization_id: int | None = None) -> None:
        super().__init__(organization_id)

    def validate(self) -> bool:
        try:
            self.organization_package.exams = self.validate_limit(self.organization_package.exams, self.organization_package.package.exams)  # type: ignore
            self.save_organization_package()
            return True
        except ValueError as e:
            raise ValueError(str(e))


class ExamService:
    """
    This class is used to create the exam with the given data.
    """

    def __init__(
        self,
        exam_data: dict,
        visibility_setter: VisibilitySetter,
        organization_validator: OrganizationValidator,
        serializer_class,
        queryset,
    ) -> None:
        self.exam_data = exam_data
        self.visibility_setter = visibility_setter
        self.organization_validator = organization_validator
        self.serializer_class = serializer_class
        self.queryset = queryset

    def create_exam(self) -> Response:
        request_data = self.visibility_setter.set_visibility(self.exam_data)

        serializer = self.serializer_class(data=request_data, context={"mutator": True})
        serializer.is_valid(raise_exception=True)

        if not get_current_user().is_superuser:  # type: ignore
            try:
                self.organization_validator.validate()
                request_data["organization"] = get_current_user_organization()
            except ValueError as e:
                ResponseMiddleware.return_now(make_error_response(message=f"Failed: {str(e)}"))

        exam = serializer.save()
        response_data = ExamSerializer(self.queryset.filter(pk=exam.id).first(), context={"selector": True}).data  # type:ignore
        return Response(response_data, status=status.HTTP_201_CREATED)
