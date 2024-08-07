from django.db import models

from core.models import BaseModel

MEDIA_MODEL = "lookups.Media"


class Organization(BaseModel):

    name = models.CharField(max_length=255)
    country = models.ForeignKey("lookups.Country", on_delete=models.CASCADE)
    logo = models.ForeignKey("lookups.Media", on_delete=models.PROTECT)

    class Meta:
        app_label = "organization"
        db_table = "organization"
