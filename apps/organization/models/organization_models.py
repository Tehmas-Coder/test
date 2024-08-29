from django.db import models

from core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization"


class OrganizationUser(BaseModel):

    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE, related_name="user_organizations")
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_users")

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_user"


class OrganizationPackage(BaseModel):

    organization = models.ForeignKey("Organization", on_delete=models.CASCADE, related_name="organization_packages")
    package = models.ForeignKey("lookups.Package", on_delete=models.CASCADE)
    users = models.PositiveIntegerField(default=0)
    questions = models.PositiveIntegerField(default=0)
    exams = models.PositiveIntegerField(default=0)
    prep_exams = models.PositiveIntegerField(default=0)
    exam_attempts = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_package"
