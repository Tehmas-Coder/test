from typing import Any
from django.db import models

from django.contrib.auth.models import AbstractUser, UserManager
from django.utils.translation import gettext_lazy as _

from django.db import models
from core.models import BaseModel
from datetime import date
from utils.email_utils import send_verification_link_or_otp_to_email
from utils.rna_utils import debug_print, generate_otp


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


class BaseUser(AbstractUser, BaseModel):
    """
    Custom user model where email is the unique identifier, inhertied from abstract user provided by auth
    """

    username = models.CharField(_("username"), max_length=150, blank=True)
    email = models.EmailField(_("email address"), unique=True)
    first_name = models.CharField(_("first name"), max_length=30, blank=True)
    last_name = models.CharField(_("last name"), max_length=30, blank=True)
    password = models.CharField(_("password"), max_length=128, blank=True)
    phone = models.CharField(_("phone"), max_length=15, blank=True)
    date_of_birth = models.DateField(_("date of birth"), blank=True, null=True)

    otp = models.CharField(_("otp"), max_length=6, blank=True)
    is_verified = models.BooleanField(_("verified"), default=False)

    is_superuser = models.BooleanField(_("superuser"), default=False)
    is_staff = models.BooleanField(_("staff status"), default=True)

    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)

    is_active = models.BooleanField(("active"), default=True)

    country = models.ForeignKey(
        "lookups.Country", on_delete=models.SET_NULL, null=True, blank=True
    )

    roles = models.ManyToManyField("Role", related_name="users", blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

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
            return (
                today.year
                - self.date_of_birth.year
                - (
                    (today.month, today.day)
                    < (self.date_of_birth.month, self.date_of_birth.day)
                )
            )
        return None

    @classmethod
    def get_user_by_email(cls, email: str):
        return cls.objects.filter(email=email).first()

    def activate(self, *args, **kwargs):
        self.is_active = True
        return super().activate(*args, **kwargs)

    def deactivate(self, *args, **kwargs):
        self.is_active = False
        return super().deactivate(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.is_active = False
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

        if not send_verification_link_or_otp_to_email(
            {
                "first_name": self.first_name,
                "last_name": self.last_name,
                "email": self.email,
                "otp": otp,
            },
            send_otp=True,
        ):
            return False

        self.otp = otp
        self.save()
        return True


class Role(BaseModel):
    name = models.CharField(max_length=255)
    permissions = models.ManyToManyField("Permission", related_name="roles", blank=True)

    class Meta:
        app_label = "user"


class Permission(BaseModel):
    name = models.CharField(max_length=255)

    class Meta:
        app_label = "user"
