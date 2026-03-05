"""
Admin management views.
FIX #13 (DRY): Uses PaginatedListMixin and ToggleAccessMixin.
FIX #15: Uses User.Role enum.
"""
import logging
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status

from core.responses import success_response, error_response, created_response
from core.permissions import IsSuperAdmin, IsAdminUser
from core.pagination import StandardPagination
from core.mixins import PaginatedListMixin
from apps.authentication.models import User
from apps.authentication.services import PasswordService
from .serializers import (
    CreateStaffAdminSerializer, AdminListSerializer,
    AdminProfileSerializer, AdminProfileUpdateSerializer,
    AdminChangePasswordSerializer,
)

logger = logging.getLogger(__name__)

ADMIN_ROLES = [User.Role.SUPER_ADMIN, User.Role.STAFF_ADMIN]


class CreateStaffAdminView(APIView):
    """Create a new staff admin account (superadmin only)."""
    permission_classes = [IsSuperAdmin]

    def post(self, request):
        serializer = CreateStaffAdminSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data
        user = User.objects.create_user(
            email=data["email"],
            password=data["password"],
            role=User.Role.STAFF_ADMIN,
            is_verified=True,
            has_access=True,
        )

        return created_response("Staff admin created successfully.", {
            "admin_id": str(user.id),
            "email": user.email,
            "role": user.role,
            "name": user.full_name or None,
            "phone_number": user.phone_number or None,
            "profile_picture": None,
            "has_access": user.has_access,
        })


class AdminListView(PaginatedListMixin, ListAPIView):
    """List all admin users with pagination."""
    permission_classes = [IsAdminUser]
    serializer_class = AdminListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return User.objects.filter(
            role__in=ADMIN_ROLES,
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["message"] = "Admin list retrieved."
        return response


class AdminProfileView(APIView):
    """Retrieve admin's own profile."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        serializer = AdminProfileSerializer(
            request.user, context={"request": request},
        )
        return success_response("Profile retrieved.", serializer.data)


class AdminProfileUpdateView(APIView):
    """Update admin's own profile (email excluded)."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        serializer = AdminProfileUpdateSerializer(
            request.user, data=request.data, partial=True,
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        user = serializer.save()
        return success_response("Profile updated successfully.", {
            "name": user.full_name,
            "email": user.email,
            "phone_number": user.phone_number,
            "role": user.role,
            "profile_picture": (
                request.build_absolute_uri(user.profile_picture.url)
                if user.profile_picture else None
            ),
        })


class AdminChangePasswordView(APIView):
    """Change admin's own password."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = AdminChangePasswordSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            PasswordService.change_password(
                user=request.user,
                old_password=serializer.validated_data["old_password"],
                new_password=serializer.validated_data["new_password"],
            )
            return success_response("Password changed successfully.")
        except ValueError as e:
            return error_response(
                "Validation failed.",
                {"old_password": [str(e)]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class DisableAdminView(APIView):
    """Disable an admin account (superadmin only)."""
    permission_classes = [IsSuperAdmin]

    def patch(self, request, pk):
        try:
            admin_user = User.objects.get(pk=pk, role__in=ADMIN_ROLES)
        except User.DoesNotExist:
            return error_response(
                "Admin not found.", status=status.HTTP_404_NOT_FOUND,
            )

        if admin_user == request.user:
            return error_response(
                "You cannot disable your own account.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_user.has_access = False
        admin_user.save(update_fields=["has_access"])
        return success_response("Admin access disabled.", {
            "admin_id": str(admin_user.id), "has_access": False,
        })


class EnableAdminView(APIView):
    """Enable an admin account (superadmin only)."""
    permission_classes = [IsSuperAdmin]

    def patch(self, request, pk):
        try:
            admin_user = User.objects.get(pk=pk, role__in=ADMIN_ROLES)
        except User.DoesNotExist:
            return error_response(
                "Admin not found.", status=status.HTTP_404_NOT_FOUND,
            )

        admin_user.has_access = True
        admin_user.save(update_fields=["has_access"])
        return success_response("Admin access enabled.", {
            "admin_id": str(admin_user.id), "has_access": True,
        })


class DeleteAdminView(APIView):
    """Permanently delete an admin account (superadmin only)."""
    permission_classes = [IsSuperAdmin]

    def delete(self, request, pk):
        try:
            admin_user = User.objects.get(pk=pk, role__in=ADMIN_ROLES)
        except User.DoesNotExist:
            return error_response(
                "Admin not found.", status=status.HTTP_404_NOT_FOUND,
            )

        if admin_user == request.user:
            return error_response(
                "You cannot delete your own account.",
                status=status.HTTP_400_BAD_REQUEST,
            )

        admin_user.delete()
        return success_response("Admin account permanently deleted.")
