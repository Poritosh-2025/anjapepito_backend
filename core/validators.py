"""
Shared validators applied across all apps.
FIX #2: Unified password validation (was only in RegisterSerializer).
FIX #11 (DRY): Centralized email normalization and phone validation.
"""
import re
import bleach
from rest_framework import serializers


def validate_password_strength(value):
    """
    Enforce password complexity: min 8 chars, 1 uppercase, 1 digit.
    Applied to ALL serializers accepting password input.
    """
    if len(value) < 8:
        raise serializers.ValidationError(
            "Password must be at least 8 characters."
        )
    if not re.search(r"[A-Z]", value):
        raise serializers.ValidationError(
            "Password must contain at least 1 uppercase letter."
        )
    if not re.search(r"[0-9]", value):
        raise serializers.ValidationError(
            "Password must contain at least 1 number."
        )
    return value


def normalize_email(value):
    """Lowercase and strip whitespace from email."""
    if value:
        return value.lower().strip()
    return value


def validate_phone_number(value):
    """E.164-compatible phone number validation."""
    if value and not re.match(r"^\+?[1-9]\d{6,14}$", value):
        raise serializers.ValidationError("Enter a valid phone number.")
    return value


def sanitize_name(value):
    """
    FIX #10: Strip HTML tags to prevent stored XSS.
    Allow letters, spaces, hyphens, apostrophes, periods.
    """
    cleaned = bleach.clean(value, tags=[], strip=True).strip()
    if not cleaned:
        raise serializers.ValidationError(
            "Name must contain visible characters."
        )
    if len(cleaned) > 255:
        raise serializers.ValidationError(
            "Name must be 255 characters or fewer."
        )
    return cleaned
