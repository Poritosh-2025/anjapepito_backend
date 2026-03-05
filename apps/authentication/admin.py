from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OTP, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        "email", "full_name", "role",
        "is_verified", "has_access", "created_at",
    ]
    list_filter = ["role", "is_verified", "has_access", "auth_provider"]
    search_fields = ["email", "full_name"]
    ordering = ["-created_at"]
    readonly_fields = ["created_at", "updated_at", "last_login"]

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal", {
            "fields": ("full_name", "phone_number", "profile_picture"),
        }),
        ("Role & Access", {
            "fields": (
                "role", "is_verified", "has_access", "auth_provider",
            ),
        }),
        ("Permissions", {
            "fields": (
                "is_active", "is_staff", "is_superuser",
                "groups", "user_permissions",
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at", "last_login"),
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email", "full_name", "role",
                "password1", "password2",
            ),
        }),
    )


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ["email", "otp_type", "created_at"]
    list_filter = ["otp_type"]
    search_fields = ["email"]
    readonly_fields = ["created_at"]


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    list_display = ["user", "token", "is_used", "created_at"]
    list_filter = ["is_used"]
    readonly_fields = ["created_at"]
