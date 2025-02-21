from decouple import config
from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models import Q
from hashids import Hashids

from middlewares.current_user_middleware import get_current_user

hashids = Hashids(min_length=8, salt="your_salt_here")


class BaseManager(models.Manager):

    def get_queryset(self):
        """
        Get the queryset of the model with the meta_status filter applied to it to get only the active records.
        :return: The queryset
        """
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
        """
        Get random records from the model.
        :param count: The number of records to get
        :param q_filter: The filter to apply to the queryset
        :param annotation: The annotation to apply to the queryset
        :return: The queryset of random records
        """
        qs = cls.objects.annotate(**annotation).filter(q_filter).order_by("?")
        if count:
            return qs[:count]
        return qs

    def save(self, *args, **kwargs):
        """
        Save the model instance with the current user as the created_by and updated_by fields.
        """
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
        """
        - Soft delete the model instance if the ENABLE_SOFT_DELETE setting is True, otherwise hard delete it.
        - Soft delete means setting the meta_status field to "deleted".
        - Hard delete means deleting the model instance from the database.
        - If the on_delete attribute of a related object is set to PROTECT, then the delete operation will be blocked.
        - If the on_delete attribute of a related object is set to CASCADE, then the delete operation will cascade to the related objects.

        :param using: The database alias to delete from
        :param keep_parents: Whether to keep the parent objects
        """
        if config("ENABLE_SOFT_DELETE", cast=bool, default=False):
            self._check_protect()
            self.meta_status = "deleted"
            self.save()
            self._cascade_soft_delete()
        else:
            super().delete(*args, **kwargs)

    def _check_protect(self):
        """
        Check if there are any related objects with the on_delete attribute set to PROTECT., if there are, then raise a ProtectedError.
        """
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
        """
        Cascade the soft delete operation to the related objects with the on_delete attribute set to CASCADE or SET_NULL.
        """
        for related_object in self._meta.related_objects:
            related_name = related_object.get_accessor_name()
            related_manager = getattr(self, related_name)
            if isinstance(related_manager, models.Manager):
                if related_object.on_delete == models.CASCADE:
                    related_manager.all().update(meta_status="deleted")
                elif related_object.on_delete == models.SET_NULL:
                    related_manager.all().update(**{related_object.field.name: None})

    def activate(self, *args, **kwargs):
        """
        Activate the model instance by setting the meta_status field to "active".
        """
        self.meta_status = "active"
        self.save()

    def deactivate(self, *args, **kwargs):
        """
        Deactivate the model instance by setting the meta_status field to "inactive".
        """
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
