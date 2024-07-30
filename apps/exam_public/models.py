from django.db import models

from core.models import BaseModel


class Candidate(BaseModel):
    user = models.OneToOneField("user.BaseUser", on_delete=models.CASCADE)
