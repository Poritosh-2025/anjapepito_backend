"""
Custom User model (email-based) + OTP + PasswordResetToken.
"""
import uuid
import secrets
from django.conf import settings
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin,
)
from django.db import models
from django.utils import timezone
from datetime import timedelta

from core.models import TimeStampedModel


class UserManager(BaseUserManager):
    """Custom manager: email is the unique identifier."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "super_admin")
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("has_access", True)
        return self.create_user(email, password, **extra_fields)


def profile_picture_upload_path(instance, filename):
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    return f"users/{instance.id}/profile.{ext}"


class User(AbstractBaseUser, PermissionsMixin, TimeStampedModel):
    """
    Core user model serving all roles: super_admin, staff_admin, user.
    Single-table inheritance via role field keeps queries simple.
    """

    class Role(models.TextChoices):
        SUPER_ADMIN = "super_admin", "Super Admin"
        STAFF_ADMIN = "staff_admin", "Staff Admin"
        USER = "user", "User"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    email = models.EmailField(unique=True, db_index=True, max_length=255)
    full_name = models.CharField(max_length=255, blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    profile_picture = models.ImageField(
        upload_to=profile_picture_upload_path, blank=True, null=True,
    )
    role = models.CharField(
        max_length=20, choices=Role.choices,
        default=Role.USER, db_index=True,
    )

    is_verified = models.BooleanField(default=False, db_index=True)
    has_access = models.BooleanField(default=True, db_index=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    auth_provider = models.CharField(
        max_length=50, default="email", db_index=True,
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"
        indexes = [
            models.Index(
                fields=["email", "is_verified"],
                name="idx_email_verified",
            ),
            models.Index(
                fields=["role", "has_access"], name="idx_role_access",
            ),
            models.Index(
                fields=["created_at"], name="idx_user_created",
            ),
            models.Index(
                fields=["role", "created_at"], name="idx_role_created",
            ),
        ]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_super_admin(self):
        return self.role == self.Role.SUPER_ADMIN

    @property
    def is_admin(self):
        return self.role in (
            self.Role.SUPER_ADMIN, self.Role.STAFF_ADMIN,
        )


class OTP(TimeStampedModel):
    """
    One-Time Password for email verification and password reset.
    """

    class OTPType(models.TextChoices):
        REGISTER = "register", "Registration"
        PASSWORD_RESET = "password_reset", "Password Reset"

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    email = models.EmailField(db_index=True)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(
        max_length=20, choices=OTPType.choices, db_index=True,
    )

    class Meta:
        db_table = "otps"
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        indexes = [
            models.Index(
                fields=["email", "otp_type"],
                name="idx_otp_email_type",
            ),
            models.Index(
                fields=["created_at"], name="idx_otp_created",
            ),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["email", "otp_type"],
                name="unique_active_otp_per_email_type",
            ),
        ]

    def __str__(self):
        return f"OTP({self.email}, {self.otp_type})"

    @property
    def is_expired(self):
        expiry = self.created_at + timedelta(
            minutes=settings.OTP_EXPIRY_MINUTES,
        )
        return timezone.now() > expiry

    @staticmethod
    def generate_code():
        """Cryptographically secure 6-digit OTP."""
        return f"{secrets.randbelow(900000) + 100000}"


class PasswordResetToken(TimeStampedModel):
    """
    Short-lived token issued after OTP verification for password reset.
    """

    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False,
    )
    user = models.ForeignKey(
        "authentication.User",
        on_delete=models.CASCADE,
        related_name="reset_tokens",
    )
    token = models.UUIDField(
        default=uuid.uuid4, unique=True, db_index=True,
    )
    is_used = models.BooleanField(default=False)

    class Meta:
        db_table = "password_reset_tokens"
        indexes = [
            models.Index(
                fields=["token", "is_used"], name="idx_reset_token",
            ),
            models.Index(
                fields=["created_at"], name="idx_reset_created",
            ),
        ]

    def __str__(self):
        return f"ResetToken({self.user.email})"

    @property
    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=15)

    @property
    def is_valid(self):
        return not self.is_used and not self.is_expired
