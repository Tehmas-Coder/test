from decouple import config
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import OuterRef, Q, Subquery
from hashids import Hashids
from rest_framework.authentication import get_user_model

from core.middlewares.current_user_middleware import get_current_user

hashids = Hashids(min_length=8, salt="your_salt_here")


class BaseManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset().filter(meta_status="active")
        created_user_subquery = get_user_model().objects.filter(pk=OuterRef("created_by")).values("username")
        updated_user_subquery = get_user_model().objects.filter(pk=OuterRef("updated_by")).values("username")

        return qs.annotate(created_by_username=Subquery(created_user_subquery[:1]), updated_by_username=Subquery(updated_user_subquery[:1]))


class BaseModel(models.Model):

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.PositiveIntegerField(null=True)

    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.PositiveIntegerField(null=True)

    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deleted", "Deleted"),
    )
    meta_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    objects = BaseManager()

    class Meta:
        abstract = True

    @classmethod
    def get_random(cls, count: int | None = None, q_filter: Q | None = Q(), annotation: dict = {}):
        qs = cls.objects.annotate(**annotation).filter(q_filter).order_by("?")
        if count:
            return qs[:count]
        return qs

    def save(self, *args, **kwargs):
        current_user = get_current_user()
        if isinstance(current_user, AnonymousUser):
            current_user = None

        if not self.pk:
            if current_user:
                self.created_by = current_user.id
            else:
                self.created_by = None

        if current_user:
            self.updated_by = current_user.id
        else:
            self.updated_by = None

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
