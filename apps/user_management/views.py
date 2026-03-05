"""
User management views for admins.
FIX #13 (DRY): Uses PaginatedListMixin.
FIX #15: Uses User.Role enum.
"""
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework import status

from core.responses import success_response, error_response
from core.permissions import IsSuperAdmin, IsAdminUser
from core.pagination import StandardPagination
from core.mixins import PaginatedListMixin
from apps.authentication.models import User
from .serializers import UserListSerializer, UserDetailSerializer


class UserListView(PaginatedListMixin, ListAPIView):
    """List all regular users with pagination."""
    permission_classes = [IsAdminUser]
    serializer_class = UserListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return User.objects.filter(
            role=User.Role.USER,
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["message"] = "User list retrieved."
        return response


class UserDetailView(APIView):
    """Retrieve a single user's details."""
    permission_classes = [IsAdminUser]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(
                "User not found.", status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserDetailSerializer(
            user, context={"request": request},
        )
        return success_response(
            "User detail retrieved.", serializer.data,
        )


class DisableUserView(APIView):
    """Disable a user account."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(
                "User not found.", status=status.HTTP_404_NOT_FOUND,
            )

        user.has_access = False
        user.save(update_fields=["has_access"])
        return success_response("User access disabled.", {
            "user_id": str(user.id), "has_access": False,
        })


class EnableUserView(APIView):
    """Enable a user account."""
    permission_classes = [IsAdminUser]

    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(
                "User not found.", status=status.HTTP_404_NOT_FOUND,
            )

        user.has_access = True
        user.save(update_fields=["has_access"])
        return success_response("User access enabled.", {
            "user_id": str(user.id), "has_access": True,
        })


class DeleteUserView(APIView):
    """Permanently delete a user account (superadmin only)."""
    permission_classes = [IsSuperAdmin]

    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk, role=User.Role.USER)
        except User.DoesNotExist:
            return error_response(
                "User not found.", status=status.HTTP_404_NOT_FOUND,
            )

        user.delete()
        return success_response("User account permanently deleted.")
