"""
Role-based permission classes.
FIX #15: References User.Role enum instead of hardcoded string literals.
"""
from rest_framework.permissions import BasePermission
from apps.authentication.models import User


class IsSuperAdmin(BasePermission):
    """Only super_admin role with active access."""
    message = "Only superadmin can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == User.Role.SUPER_ADMIN
            and request.user.has_access
        )


class IsAdminUser(BasePermission):
    """super_admin OR staff_admin with active access."""
    message = "You do not have permission to view this resource."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in (
                User.Role.SUPER_ADMIN, User.Role.STAFF_ADMIN
            )
            and request.user.has_access
        )


class IsAuthenticatedUser(BasePermission):
    """Any authenticated user with active access."""
    message = "Authentication credentials were not provided."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.has_access
        )
