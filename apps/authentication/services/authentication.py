"""
Authentication service handling login, logout, and token management.
"""
import logging
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken

from apps.authentication.models import User

logger = logging.getLogger(__name__)


class AuthenticationService:
    """Handles login, social auth, logout, and JWT tokens."""

    @staticmethod
    def login_user(email, password):
        """Authenticate and return JWT tokens."""
        email = email.lower().strip()

        user = User.objects.filter(email=email).first()
        if not user:
            raise ValueError("Invalid email or password.")

        # Check boolean flags first (indexed, O(1)) before
        # expensive PBKDF2 comparison
        if not user.is_verified:
            raise PermissionError(
                "Please verify your email before logging in."
            )

        if not user.has_access:
            raise PermissionError("Account has been disabled.")

        user = authenticate(email=email, password=password)
        if not user:
            raise ValueError("Invalid email or password.")

        return AuthenticationService._get_tokens_for_user(user), user

    @staticmethod
    def social_login(provider, access_token):
        """
        Validate OAuth token with provider and login/register user.
        """
        raise NotImplementedError(
            "Social login requires dj-rest-auth social serializers. "
            "Configure via /api/v1/auth/social/google/ and "
            "/api/v1/auth/social/apple/"
        )

    @staticmethod
    def logout_user(refresh_token_str):
        """Blacklist the refresh token."""
        try:
            token = RefreshToken(refresh_token_str)
            token.blacklist()
        except Exception:
            raise ValueError("Invalid or already blacklisted token.")

    @staticmethod
    def _get_tokens_for_user(user):
        """Generate JWT token pair."""
        refresh = RefreshToken.for_user(user)
        return {
            "access_token": str(refresh.access_token),
            "refresh_token": str(refresh),
        }
