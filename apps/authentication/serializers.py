"""
Authentication serializers with thorough validation.
FIX #2: All password fields use shared validate_password_strength.
FIX #10: full_name sanitized via sanitize_name.
FIX #13 (DRY): Email normalization and phone validation extracted.
"""
from rest_framework import serializers
from django.conf import settings
from core.validators import (
    validate_password_strength,
    normalize_email,
    validate_phone_number,
    sanitize_name,
)
from .models import User


class RegisterSerializer(serializers.Serializer):
    """User registration with full password strength enforcement."""
    full_name = serializers.CharField(max_length=255)
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    re_type_password = serializers.CharField(min_length=8, write_only=True)

    def validate_email(self, value):
        return normalize_email(value)

    def validate_full_name(self, value):
        return sanitize_name(value)

    def validate_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        if data["password"] != data["re_type_password"]:
            raise serializers.ValidationError(
                {"re_type_password": "Passwords do not match."}
            )
        return data


class SuperadminRegisterSerializer(RegisterSerializer):
    """
    FIX #1: Requires setup_key and enforces one-time creation.
    """
    setup_key = serializers.CharField(write_only=True)

    def validate_setup_key(self, value):
        if value != settings.SUPERADMIN_SETUP_KEY:
            raise serializers.ValidationError("Invalid setup key.")
        return value

    def validate(self, data):
        data = super().validate(data)
        if User.objects.filter(role=User.Role.SUPER_ADMIN).exists():
            raise serializers.ValidationError(
                "A superadmin account already exists. "
                "Use admin panel to manage additional admins."
            )
        return data


class VerifyOTPSerializer(serializers.Serializer):
    """OTP verification with strict numeric validation."""
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)
    otp_type = serializers.ChoiceField(
        choices=["register", "password_reset"],
    )

    def validate_email(self, value):
        return normalize_email(value)

    def validate_otp_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError(
                "OTP must be 6 numeric digits."
            )
        return value


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_type = serializers.ChoiceField(
        choices=["register", "password_reset"],
    )

    def validate_email(self, value):
        return normalize_email(value)


class LoginSerializer(serializers.Serializer):
    """Supports both standard and social login."""
    email = serializers.EmailField(required=False)
    password = serializers.CharField(required=False, write_only=True)
    provider = serializers.ChoiceField(
        choices=["google", "apple"], required=False,
    )
    access_token = serializers.CharField(required=False)

    def validate_email(self, value):
        return normalize_email(value)

    def validate(self, data):
        provider = data.get("provider")
        if provider:
            if not data.get("access_token"):
                raise serializers.ValidationError(
                    {"access_token": "Required for social login."}
                )
        else:
            if not data.get("email") or not data.get("password"):
                raise serializers.ValidationError(
                    "Email and password are required for standard login."
                )
        return data


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        return normalize_email(value)


class VerifyResetOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(min_length=6, max_length=6)

    def validate_email(self, value):
        return normalize_email(value)


class PasswordResetSerializer(serializers.Serializer):
    """FIX #2: Enforces password strength on reset."""
    reset_token = serializers.UUIDField()
    new_password = serializers.CharField(min_length=8, write_only=True)
    confirm_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError(
                {"confirm_password": "Passwords do not match."}
            )
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """FIX #2: Enforces password strength on change."""
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(min_length=8, write_only=True)
    re_type_password = serializers.CharField(min_length=8, write_only=True)

    def validate_new_password(self, value):
        return validate_password_strength(value)

    def validate(self, data):
        if data["new_password"] != data["re_type_password"]:
            raise serializers.ValidationError(
                {"re_type_password": "Passwords do not match."}
            )
        return data


class TokenRefreshSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = User
        fields = [
            "user_id", "full_name", "email", "phone_number",
            "profile_picture", "role", "is_verified", "date_joined",
        ]
        read_only_fields = [
            "email", "role", "is_verified", "date_joined",
        ]
        extra_kwargs = {
            "date_joined": {"source": "created_at"},
        }


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["full_name", "phone_number", "profile_picture"]
        extra_kwargs = {
            "full_name": {"required": False},
            "phone_number": {"required": False},
            "profile_picture": {"required": False},
        }

    def validate_full_name(self, value):
        return sanitize_name(value)

    def validate_phone_number(self, value):
        return validate_phone_number(value)
