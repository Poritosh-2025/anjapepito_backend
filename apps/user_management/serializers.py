"""Serializers for user management (admin-facing)."""
from rest_framework import serializers
from apps.authentication.models import User


class UserListSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="id")
    user_full_name = serializers.CharField(source="full_name")
    user_email = serializers.EmailField(source="email")
    user_phone_number = serializers.CharField(source="phone_number")

    class Meta:
        model = User
        fields = [
            "user_id", "user_full_name", "user_email",
            "user_phone_number", "has_access",
        ]


class UserDetailSerializer(serializers.ModelSerializer):
    user_id = serializers.UUIDField(source="id")
    date_joined = serializers.DateTimeField(source="created_at")

    class Meta:
        model = User
        fields = [
            "user_id", "full_name", "email", "phone_number",
            "profile_picture", "role", "is_verified",
            "has_access", "date_joined",
        ]
