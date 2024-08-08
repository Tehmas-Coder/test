from django.db import models

from core.models import BaseModel


class Organization(BaseModel):
    name = models.CharField(max_length=255)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization"


class OrganizationUser(BaseModel):

    user = models.ForeignKey("user.BaseUser", on_delete=models.CASCADE)
    organization = models.ForeignKey("Organization", on_delete=models.CASCADE)

    class Meta:
        app_label = "organization"
        db_table = "organization_organization_user"
