from datetime import date, timedelta
from typing import Any

from django.contrib.auth.models import AbstractUser, UserManager
from django.db import IntegrityError, models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from apps.user.helpers.queryset_functions import (
    get_role_detailed_queryset,
    get_user_detailed_queryset,
)
from core.models import BaseModel, BaseUserModel
from middlewares.response_middleware import ResponseMiddleware
from utils.datetime_utils import (
    convert_any_datetime_to_utc,
    get_current_utc_datetime,
    get_current_utc_datetime_timestamp,
)
from utils.email_notifications import EmailNotification
from utils.rna_utils import generate_otp, make_error_response


def upload_to(instance, filename):
    """
    Generate a file path for uploaded media.
    """
    folder_name = instance.__class__.__name__.lower()
    timestamp = get_current_utc_datetime_timestamp()
    return f"{folder_name}/{timestamp}_{filename}"


class Media(BaseModel):
    """
    Model to store any type of media in the system.

    - id: Autofield (PK)
    - type: MediaType (FK)
    - name: CharField
    - file: FileField
    - extension: CharField
    - size: IntegerField
    """

    type = models.ForeignKey("lookups.MediaType", on_delete=models.CASCADE)

    name = models.CharField(max_length=100)
    file = models.FileField(upload_to=upload_to)
    extension = models.CharField(max_length=10, blank=True)
    size = models.IntegerField(default=0)

    class Meta:
        app_label = "user"


class CustomUserManager(UserManager):
    """
    - Custom user manager where email is the unique identifier, inherited from UserManager provided by auth
    - Filters out users with meta_status as 'active'
    """

    def create_superuser(self, email: str, password: str | None, **extra_fields: Any) -> Any:
        """
        Create and return a superuser with the given email and password.

        Args:
            email (str): The email address of the superuser.
            password (str | None): The password for the superuser. Can be None.
            **extra_fields (Any): Additional fields for the superuser.

        Returns:
            Any: The created superuser instance.
        """

        username = email
        return super().create_superuser(username, email, password, **extra_fields)

    def get_queryset(self):
        """
        - Filters out users with meta_status as 'active'.
        - Returns the queryset of the model.
        """
        qs = super().get_queryset().filter(meta_status="active")
        return qs


class BaseUser(BaseUserModel, AbstractUser):
    """
    Custom user model where email is the unique identifier, inherited from abstract user provided by auth

    - id: Autofield (PK)
    - country: Country (FK)
    - profile_picture: Media (FK)
    - username: CharField
    - email: EmailField
    - first_name: CharField
    - last_name: CharField
    - password: CharField
    - phone: CharField
    - date_of_birth: DateField
    - otp: CharField
    - otp_expiry: DateTimeField
    - date_joined: DateTimeField
    - last_login: DateTimeField
    - creation_context: CharField
        Choices
            - "self"
            - "facebook"
            - "google"
            - "public_exam"
    - is_verified: BooleanField
    - is_superuser: BooleanField
    - roles: Role (M2M)
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
    otp_expiry = models.DateTimeField(_("otp expiry"), blank=True, null=True)
    date_joined = models.DateTimeField(_("date joined"), auto_now_add=True)
    last_login = models.DateTimeField(_("last login"), blank=True, null=True)
    CREATION_CONTEXT_CHOICES = [
        ("self", "Self"),
        ("facebook", "Facebook"),
        ("google", "Google"),
        ("public_exam", "Public Exam"),
    ]
    creation_context = models.CharField(_("creation context"), max_length=20, choices=CREATION_CONTEXT_CHOICES, default="self")

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
        """
        Returns the full name of the user by combining first name and last name.
        """
        return f"{self.first_name} {self.last_name}"

    @property
    def is_otp_expired(self):
        """
        - Checks if the OTP is expired based on the expiry date.
        - Returns True if the OTP is expired, False otherwise.
        """
        if self.otp_expiry:
            return convert_any_datetime_to_utc(self.otp_expiry) < get_current_utc_datetime()
        return True

    @property
    def age(self):
        """
        - Calculates the age of the user based on the date of birth.
        - Returns the age of the user.
        """
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None

    @property
    def get_user_role_slugs(self):
        """
        Returns a list of role slugs associated with the user.
        """
        return list(self.roles.values_list("slug", flat=True))

    @classmethod
    def get_user_by_email(cls, email: str):
        """
        Returns the user with the provided email address if it exists, None otherwise.
        """
        return cls.objects.filter(email=email).first()

    @classmethod
    def get_detail_queryset(cls, country=False, roles=False, role_permissions=False, role_permissions_permission=False, user_candidates=False):
        """
        Returns a queryset with detailed information about the user.
        """
        return get_user_detailed_queryset(cls, country, roles, role_permissions, role_permissions_permission, user_candidates)

    def verify_otp(self, otp: str) -> bool:
        """
        - Verifies the OTP provided by the user.
        - If the OTP is correct and not expired, marks the user as verified.
        - Returns True if the OTP is verified, False otherwise.
        """
        if self.is_otp_expired:
            return False
        if self.otp != otp:
            return False

        self.is_verified = True
        self.save()
        return True

    def send_otp(self, otp: str | None = None) -> bool:
        """
        - Sends an OTP to the user's email for verification.
        - If OTP is not provided, generates a new OTP.
        - Returns True if the OTP is sent successfully, False otherwise.
        """
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
        email_notification_ninja = EmailNotification(send_email_data_dict)
        if not email_notification_ninja.send_otp():
            return False
        del email_notification_ninja

        self.otp = otp
        self.otp_expiry = get_current_utc_datetime() + timedelta(minutes=5)
        self.save()
        return True

    def add_role(self, role):
        """
        Adds a role to the user.
        """
        self.roles.add(role)
        self.save()


# ---------------------------------------------------------------------------- #
#                                  PERMISSIONS                                 #
# ---------------------------------------------------------------------------- #
class Permission(BaseModel):
    """
    Represents a permission that can be assigned to roles.

    - id: Autofield (PK)
    - name: CharField
    - context_value: CharField
    """

    name = models.CharField(max_length=255)
    context_value = models.CharField(max_length=255)

    class Meta:
        app_label = "user"


class Role(BaseModel):
    """
    Represents a role that can be assigned to users.

    - id: Autofield (PK)
    - organization: Organization (FK)
    - name: CharField
    - slug: SlugField
    - is_system_role: BooleanField
    - permissions: Permission (M2M)
    """

    organization = models.ForeignKey("lookups.Organization", on_delete=models.PROTECT, null=True, blank=True, related_name="organization_roles")

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=100, null=True, unique=True)

    is_system_role = models.BooleanField(default=False)

    permissions = models.ManyToManyField(Permission, blank=True, through="RolePermission")

    def save(self, *args, **kwargs):
        """
        - Generates a slug for the role if it does not exist.
        - Raises an error if a role with the same name already exists in the database.
        """
        if not self.pk:
            self.slug = slugify(f"{self.organization_id}-{self.name}" if self.organization else slugify(self.name))  # type: ignore
        try:
            super().save(*args, **kwargs)
        except IntegrityError:
            ResponseMiddleware.return_now(make_error_response(message="Role with this name already exists"))

    class Meta:
        app_label = "user"

    @classmethod
    def get_detail_queryset(cls, organization=False, permissions=False, role_permissions=False, role_permissions_permission=False):
        """
        - Returns a queryset containing detailed information about roles,
        - including associated organizations and permissions.
        """
        return get_role_detailed_queryset(cls, organization, permissions, role_permissions, role_permissions_permission)


class Resource(BaseModel):
    """
    Represents a resource that can be accessed by users based on permissions.

    - id: Autofield (PK)
    - permission: Permission (FK)
    - name: CharField
    - regex: CharField
    - method: CharField
    """

    permission = models.ForeignKey(Permission, on_delete=models.PROTECT, null=True, blank=True, related_name="permission_resources")

    name = models.CharField(max_length=255)
    regex = models.CharField(max_length=255)
    method = models.CharField(max_length=255)

    class Meta:
        app_label = "user"


# ---------------------------------------------------------------------------- #
#                                     MAPS                                     #
# ---------------------------------------------------------------------------- #


class RolePermission(BaseModel):
    """
    Represents a mapping between roles and permissions.

    - id: Autofield (PK)
    - role: Role (FK)
    - permission: Permission (FK)
    - is_active: BooleanField
    """

    role = models.ForeignKey(Role, on_delete=models.PROTECT, related_name="role_permissions")
    permission = models.ForeignKey(Permission, on_delete=models.PROTECT)

    is_active = models.BooleanField(default=False)

    class Meta:
        app_label = "user"
        db_table = "user_role_permission"


class UserRole(BaseModel):
    """
    Represents a mapping between users and roles.

    - id: Autofield (PK)
    - user: BaseUser (FK)
    - role: Role (FK)
    """

    user = models.ForeignKey(BaseUser, on_delete=models.PROTECT)
    role = models.ForeignKey(Role, on_delete=models.PROTECT)

    class Meta:
        app_label = "user"
        db_table = "user_baseuser_role"
