"""
Serializers for admin management endpoints.
FIX #2: CreateStaffAdminSerializer enforces password strength.
FIX #6: AdminProfileUpdateSerializer removes email from writable fields.
FIX #13 (DRY): Uses shared validators.
"""
from rest_framework import serializers
from core.validators import (
    validate_password_strength,
    normalize_email,
    validate_phone_number,
    sanitize_name,
)
from apps.authentication.models import User


class CreateStaffAdminSerializer(serializers.Serializer):
    """FIX #2: Password strength enforced on staff creation."""
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    role = serializers.ChoiceField(choices=["staff_admin"])

    def validate_email(self, value):
        value = normalize_email(value)
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value

    def validate_password(self, value):
        return validate_password_strength(value)


class AdminListSerializer(serializers.ModelSerializer):
    admin_id = serializers.UUIDField(source="id")
    admin_name = serializers.CharField(source="full_name")
    admin_email = serializers.EmailField(source="email")
    admin_contact_number = serializers.CharField(source="phone_number")
    has_access_to = serializers.CharField(source="role")

    class Meta:
        model = User
        fields = [
            "admin_id", "admin_name", "admin_email",
            "admin_contact_number", "has_access_to", "has_access",
        ]


class AdminProfileSerializer(serializers.ModelSerializer):
    admin_id = serializers.UUIDField(source="id", read_only=True)
    name = serializers.CharField(source="full_name")

    class Meta:
        model = User
        fields = [
            "admin_id", "name", "email",
            "phone_number", "role", "profile_picture",
        ]
        read_only_fields = ["role", "email"]


class AdminProfileUpdateSerializer(serializers.ModelSerializer):
    """
    FIX #6: email REMOVED from writable fields.
    Email changes require a separate OTP-verified flow.
    """
    name = serializers.CharField(source="full_name", required=False)

    class Meta:
        model = User
        fields = ["name", "phone_number", "profile_picture"]
        extra_kwargs = {
            "phone_number": {"required": False},
            "profile_picture": {"required": False},
        }

    def validate_name(self, value):
        return sanitize_name(value)

    def validate_phone_number(self, value):
        return validate_phone_number(value)


class AdminChangePasswordSerializer(serializers.Serializer):
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
