from apps.lookups.custom.lookups_classes import (
    OrganizationPackageLimitValidator,
    VisibilitySetter,
)


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
