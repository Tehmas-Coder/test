from datetime import date, datetime
from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from core.models import BaseModel, BaseUserModel
from utils.email_notifications import EmailNotification
from utils.rna_utils import generate_otp


def upload_to(instance, filename):
    folder_name = instance.__class__.__name__.lower()
    timestamp = int(datetime.now().timestamp())
    return f"{folder_name}/{timestamp}_{filename}"


class Media(BaseModel):
    name = models.CharField(max_length=100)
    file = models.FileField(upload_to=upload_to)
    type = models.ForeignKey("lookups.MediaType", on_delete=models.CASCADE)
    extension = models.CharField(max_length=10, blank=True)
    size = models.IntegerField(default=0)

    class Meta:
        app_label = "user"


class CustomUserManager(UserManager):
    """
    Custom user manager where email is the unique identifier, inherited from UserManager provided by auth
    """

    def create_superuser(
        self,
        email: str,
        password: str | None,
        **extra_fields: Any,
    ) -> Any:
        username = email
        return super().create_superuser(username, email, password, **extra_fields)


class BaseUser(BaseUserModel, AbstractUser):
    """
    Custom user model where email is the unique identifier, inhertied from abstract user provided by auth
    """

    country = models.ForeignKey("lookups.Country", on_delete=models.SET_NULL, null=True, blank=True)
    profile_picture = models.ForeignKey("user.Media", on_delete=models.SET_NULL, null=True, blank=True)

    username = models.CharField(_("username"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True)
    password = models.CharField(_("password"), max_length=128, blank=True)
    phone = models.CharField(_("phone"), max_length=15, blank=True)
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)
    otp = models.CharField(_("otp"), max_length=6, blank=True)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    is_verified = models.BooleanField(_("verified"), default=False)
    is_superuser = models.BooleanField(_("superuser"), default=False)

    roles = models.ManyToManyField("Role", related_name="users", blank=True, through="UserRole", through_fields=("user", "role"))

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["password"]

    class Meta:
        app_label = "user"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    @classmethod
    def get_user_by_email(cls, email: str):
        return cls.objects.filter(email=email).first()

    def activate(self, *args, **kwargs):
        return super().activate(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        return super().deactivate(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return super().delete(*args, **kwargs)

    def verify_otp(self, otp: str) -> bool:
        if self.otp != otp:
            return False

        self.is_verified = True
        self.otp = ""
        self.save()
        return True

    def send_otp(self, otp: str | None = None) -> bool:

        if self.is_verified:
            return False
        if not otp:
            otp = generate_otp()

        send_email_data_dict = {
            "first_name": self.first_name,
            "last_name": self.last_name,
            "email": self.email,
            "OTP": otp,
        }
        emai_notification_ninja = EmailNotification(send_email_data_dict)
        if not emai_notification_ninja.send_otp():
            return False
        del emai_notification_ninja

        self.otp = otp
        self.save()
        return True

    def add_role(self, role):
        self.roles.add(role)
        self.save()


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #
class Role(BaseModel):
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, null=True, unique=True)

    is_system_role = models.BooleanField(default=False)

    permissions = models.ManyToManyField("Permission", blank=True, through="RolePermission")

    def save(self, *args, **kwargs):
        self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        app_label = "user"


class UserRole(BaseModel):
    user = models.ForeignKey(BaseUser, on_delete=models.PROTECT)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta:
        app_label = "user"
        db_table = "user_baseuser_role"


class Permission(BaseModel):
    name = models.CharField(max_length=255)
    context_value = models.CharField(max_length=255)

    class Meta:
        app_label = "user"


class RolePermission(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT)

    is_active = models.BooleanField(default=False)

    class Meta:
        app_label = "user"
        db_table = "user_role_permission"


# ---------------------------------------------------------------------------- #
#                                  ROLE RESOURCE                               #
# ---------------------------------------------------------------------------- #


class Resource(BaseModel):
    name = models.CharField(max_length=255)
    regex = models.CharField(max_length=255)
    method = models.CharField(max_length=255)

    class Meta:
        app_label = "user"


class RoleResource(BaseModel):
    role = models.ForeignKey(Role, on_delete=models.PROTECT)
    resource = models.ForeignKey(Resource, on_delete=models.PROTECT)

    class Meta:
        app_label = "user"
        db_table = "user_role_resource"
