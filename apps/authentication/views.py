"""
Authentication API views.
Each view is thin: validate input -> call service -> return envelope.
FIX #4: OTPRateThrottle added to VerifyOTPView and VerifyResetOTPView.
FIX #7: Password reset and resend return generic success messages.
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from core.responses import success_response, error_response, created_response
from core.permissions import IsAuthenticatedUser
from core.throttling import OTPRateThrottle
from .serializers import (
    RegisterSerializer, SuperadminRegisterSerializer,
    VerifyOTPSerializer, ResendOTPSerializer, LoginSerializer,
    LogoutSerializer, PasswordResetRequestSerializer,
    VerifyResetOTPSerializer, PasswordResetSerializer,
    ChangePasswordSerializer, TokenRefreshSerializer,
    UserProfileSerializer, UserProfileUpdateSerializer,
)
from .services import (
    RegistrationService, AuthenticationService, PasswordService,
)

logger = logging.getLogger(__name__)


class RegisterSuperadminView(APIView):
    """
    One-time superadmin setup.
    FIX #1: Requires setup_key; rejects if superadmin exists.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SuperadminRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            user = RegistrationService.register_superadmin(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                full_name=serializer.validated_data["full_name"],
            )
            return created_response(
                "Superadmin registered. Please verify your email.",
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "role": user.role,
                },
            )
        except ValueError as e:
            return error_response(
                str(e), status=status.HTTP_400_BAD_REQUEST,
            )


class RegisterView(APIView):
    """Standard user registration."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            user = RegistrationService.register_user(
                email=serializer.validated_data["email"],
                password=serializer.validated_data["password"],
                full_name=serializer.validated_data["full_name"],
            )
            return created_response(
                "Registration successful. Check your email for OTP.",
                {
                    "user_id": str(user.id),
                    "email": user.email,
                    "is_verified": False,
                },
            )
        except ValueError as e:
            return error_response(
                str(e), status=status.HTTP_400_BAD_REQUEST,
            )


class ResendOTPView(APIView):
    """Resend OTP with rate limiting."""
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        RegistrationService.resend_otp(
            email=serializer.validated_data["email"],
            otp_type=serializer.validated_data["otp_type"],
        )
        # FIX #7: Always return success (anti-enumeration)
        return success_response(
            "If an account exists, a new OTP has been sent."
        )


class VerifyOTPView(APIView):
    """
    Verify OTP for registration or password reset.
    FIX #4: Rate-limited to prevent brute-force.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            RegistrationService.verify_otp(
                email=serializer.validated_data["email"],
                otp_code=serializer.validated_data["otp_code"],
                otp_type=serializer.validated_data["otp_type"],
            )
            return success_response(
                "Email verified successfully. You can now log in.",
                {"is_verified": True},
            )
        except ValueError as e:
            return error_response(
                "Invalid or expired OTP.",
                {"otp_code": [str(e)]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class LoginView(APIView):
    """Standard and social login."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        data = serializer.validated_data

        if data.get("provider"):
            try:
                result = AuthenticationService.social_login(
                    data["provider"], data["access_token"],
                )
                return success_response(
                    f"Logged in via {data['provider'].title()}.",
                    result,
                )
            except Exception as e:
                return error_response(
                    str(e), status=status.HTTP_400_BAD_REQUEST,
                )

        try:
            tokens, user = AuthenticationService.login_user(
                data["email"], data["password"],
            )
            pic = None
            if user.profile_picture:
                pic = request.build_absolute_uri(user.profile_picture.url)

            return success_response("Login successful.", {
                "user_id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "profile_picture": pic,
                **tokens,
            })
        except PermissionError as e:
            return error_response(
                str(e), status=status.HTTP_403_FORBIDDEN,
            )
        except ValueError:
            return error_response(
                "Authentication failed.",
                {"non_field_errors": ["Invalid email or password."]},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class LogoutView(APIView):
    """Blacklist refresh token."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            AuthenticationService.logout_user(
                serializer.validated_data["refresh_token"],
            )
            return success_response("Logged out successfully.")
        except ValueError as e:
            return error_response(
                str(e), status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetRequestView(APIView):
    """Request password reset OTP."""
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        PasswordService.request_password_reset(
            serializer.validated_data["email"],
        )
        # FIX #7: Always return success (anti-enumeration)
        return success_response(
            "If an account exists, a reset OTP has been sent."
        )


class VerifyResetOTPView(APIView):
    """
    Verify password-reset OTP and issue reset token.
    FIX #4: Rate-limited.
    """
    permission_classes = [AllowAny]
    throttle_classes = [OTPRateThrottle]

    def post(self, request):
        serializer = VerifyResetOTPSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            reset_token = PasswordService.verify_reset_otp(
                email=serializer.validated_data["email"],
                otp_code=serializer.validated_data["otp_code"],
            )
            return success_response(
                "OTP verified. Use reset_token to set new password.",
                {"reset_token": reset_token},
            )
        except ValueError as e:
            return error_response(
                "Invalid or expired OTP.",
                {"otp_code": [str(e)]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class PasswordResetView(APIView):
    """Set new password using reset token."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            PasswordService.reset_password(
                reset_token_str=str(
                    serializer.validated_data["reset_token"]
                ),
                new_password=serializer.validated_data["new_password"],
            )
            return success_response(
                "Password reset successfully. Please log in."
            )
        except ValueError as e:
            return error_response(
                "Validation failed.",
                {"reset_token": [str(e)]},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ChangePasswordView(APIView):
    """Change password for authenticated user."""
    permission_classes = [IsAuthenticatedUser]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
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


class TokenRefreshView(APIView):
    """Refresh JWT access token."""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = TokenRefreshSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        try:
            token = RefreshToken(
                serializer.validated_data["refresh_token"],
            )
            return success_response(
                "Token refreshed successfully.",
                {"access_token": str(token.access_token)},
            )
        except TokenError:
            return error_response(
                "Refresh token invalid or expired. Please log in.",
                status=status.HTTP_401_UNAUTHORIZED,
            )


class UserProfileView(APIView):
    """Retrieve authenticated user profile."""
    permission_classes = [IsAuthenticatedUser]

    def get(self, request):
        serializer = UserProfileSerializer(
            request.user, context={"request": request},
        )
        return success_response(
            "Profile retrieved successfully.", serializer.data,
        )


class UserProfileUpdateView(APIView):
    """Update authenticated user profile."""
    permission_classes = [IsAuthenticatedUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request):
        serializer = UserProfileUpdateSerializer(
            request.user, data=request.data, partial=True,
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        serializer.save()
        return success_response(
            "Profile updated successfully.", serializer.data,
        )
