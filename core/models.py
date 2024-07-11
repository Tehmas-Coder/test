from django.contrib.auth.models import AnonymousUser
from django.db import models
from hashids import Hashids
from decouple import config
from core.middlewares.current_user_middleware import get_current_user
from utils.rna_utils import debug_print

hashids = Hashids(min_length=8, salt="your_salt_here")


class BaseModel(models.Model):

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=32, default="system")

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.CharField(max_length=32, default="system")

    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deleted", "Deleted"),
    )
    meta_status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default="active"
    )

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if isinstance(current_user, AnonymousUser):
            current_user = None

        if not self.pk:
            if current_user:
                self.created_by = current_user.full_name
            else:
                self.created_by = "system"

        if current_user:
            self.updated_by = current_user.full_name
        else:
            self.updated_by = "system"

        super().save(*args, **kwargs)

    @property
    def is_active(self) -> bool:
        return self.meta_status == "active"

    @property
    def is_inactive(self) -> bool:
        return self.meta_status == "inactive"

    @property
    def is_deleted(self) -> bool:
        return self.meta_status == "deleted"

    def delete(self, *args, **kwargs):
        if config("ENABLE_SOFT_DELETE", cast=bool, default=False):
            self.meta_status = "deleted"
            self.save()
        else:
            super().delete(*args, **kwargs)

    def activate(self, *args, **kwargs):
        self.meta_status = "active"
        self.save()

    def deactivate(self, *args, **kwargs):
        self.meta_status = "inactive"
        self.save()
