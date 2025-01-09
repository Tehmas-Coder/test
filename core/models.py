from decouple import config
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import OuterRef, Q, Subquery
from hashids import Hashids

from middlewares.current_user_middleware import get_current_user

hashids = Hashids(min_length=8, salt="your_salt_here")


class BaseManager(models.Manager):

    def get_queryset(self):
        # qs = super().get_queryset().filter(meta_status="active").select_related("created_by", "updated_by")
        qs = super().get_queryset().filter(meta_status="active")
        return qs


class BaseModel(models.Model):
    """
    Base model for all models in the project with common fields and methods.
    The structure to be followed by all models in the project is as follows:
    - Add a white space after every type of fields definition.
    - Foreign key fields should be defined at the top of the model.
    - Then the common fields except the boolean fields should be defined.
    - Then the boolean fields (flags) should be defined.
    - Then many-to-many fields should be defined.
    - Then the Meta class should be defined.
    - Then the methods should be defined.
    """

    created_by = models.ForeignKey("user.BaseUser", on_delete=models.SET_NULL, null=True, related_name="%(class)s_created_by")
    updated_by = models.ForeignKey("user.BaseUser", on_delete=models.SET_NULL, null=True, related_name="%(class)s_updated_by")

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
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
                self.created_by = current_user
            else:
                self.created_by = None

        if current_user:
            self.updated_by = current_user
        else:
            self.updated_by = None

        super().save(*args, **kwargs)

    @property
    def is_inactive(self) -> bool:
        return self.meta_status == "inactive"

    @property
    def is_deleted(self) -> bool:
        return self.meta_status == "deleted"

    def delete(self, using=None, keep_parents=False, *args, **kwargs):
        if config("ENABLE_SOFT_DELETE", cast=bool, default=False):
            self._check_protect()
            self.meta_status = "deleted"
            self.save()
            self._cascade_soft_delete()
        else:
            super().delete(*args, **kwargs)

    def _check_protect(self):
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if not isinstance(related_manager, models.Manager):
                continue
            if related_object.on_delete != models.PROTECT:
                continue
            if related_manager.exists():
                raise models.ProtectedError(
                    f"Cannot delete {self} because protected related {related_object.related_model.__name__} exists.",
                    protected_objects=set(related_manager.all()),
                )

    def _cascade_soft_delete(self):
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if isinstance(related_manager, models.Manager):
                if related_object.on_delete == models.CASCADE:
                    related_manager.all().update(meta_status="deleted")
                elif related_object.on_delete == models.SET_NULL:
                    related_manager.all().update(**{related_object.field.name: None})

    def activate(self, *args, **kwargs):
        self.meta_status = "active"
        self.save()

    def deactivate(self, *args, **kwargs):
        self.meta_status = "inactive"
        self.save()


class BaseUserManager(models.Manager):

    def get_queryset(self):
        qs = super().get_queryset().filter(meta_status="active")
        return qs


class BaseUserModel(models.Model):

    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = (
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("deleted", "Deleted"),
    )
    meta_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="active")

    objects = BaseUserManager()

    class Meta:
        abstract = True

    @classmethod
    def get_random(cls, count: int | None = None, q_filter: Q | None = Q(), annotation: dict = {}):
        qs = cls.objects.annotate(**annotation).filter(q_filter).order_by("?")
        if count:
            return qs[:count]
        return qs

    @property
    def is_inactive(self) -> bool:
        return self.meta_status == "inactive"

    @property
    def is_deleted(self) -> bool:
        return self.meta_status == "deleted"

    def delete(self, using=None, keep_parents=False, *args, **kwargs):
        if config("ENABLE_SOFT_DELETE", cast=bool, default=False):
            self._check_protect()
            self.meta_status = "deleted"
            self.save()
            self._cascade_soft_delete()
        else:
            super().delete(*args, **kwargs)

    def _check_protect(self):
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if not isinstance(related_manager, models.Manager):
                continue
            if related_object.on_delete != models.PROTECT:
                continue
            if related_manager.exists():
                raise models.ProtectedError(
                    f"Cannot delete {self} because protected related {related_object.related_model.__name__} exists.",
                    protected_objects=set(related_manager.all()),
                )

    def _cascade_soft_delete(self):
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if isinstance(related_manager, models.Manager):
                if related_object.on_delete == models.CASCADE:
                    related_manager.all().update(meta_status="deleted")
                elif related_object.on_delete == models.SET_NULL:
                    related_manager.all().update(**{related_object.field.name: None})

    def activate(self, *args, **kwargs):
        self.meta_status = "active"
        self.save()

    def deactivate(self, *args, **kwargs):
        self.meta_status = "inactive"
        self.save()
