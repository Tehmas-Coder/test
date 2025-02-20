from django.db import models

from core.models import BaseModel


class OrganizationUser(BaseModel):
    """
    Represents a mapping between organizations and users.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - user: BaseUser (FK)
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, related_name="organization_users")
    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_organizations")

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_user"


class OrganizationPackage(BaseModel):
    """
    Represents a package assigned to an organization.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - package: Package (FK)
    - users: PositiveIntegerField
    - questions: PositiveIntegerField
    - exams: PositiveIntegerField
    - prep_exams: PositiveIntegerField
    - exam_attempts: PositiveIntegerField
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.CASCADE, related_name="organization_packages")
    package = models.ForeignKey("lookups.Package", on_delete=models.CASCADE)

    users = models.PositiveIntegerField(default=0)
    questions = models.PositiveIntegerField(default=0)
    exams = models.PositiveIntegerField(default=0)
    prep_exams = models.PositiveIntegerField(default=0)
    exam_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_package"
