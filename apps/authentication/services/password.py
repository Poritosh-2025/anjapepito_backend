"""
Password management service: reset and change flows.
"""
import logging
from django.db import transaction

from apps.authentication.models import User, OTP, PasswordResetToken
from apps.authentication.tasks import send_otp_email_task
from .registration import RegistrationService

logger = logging.getLogger(__name__)


class PasswordService:
    """Handles password reset request, verification, and change."""

    @staticmethod
    def request_password_reset(email):
        """
        Send password reset OTP.
        FIX #7: Generic response to prevent email enumeration.
        """
        email = email.lower().strip()

        if not User.objects.filter(
            email=email, is_verified=True,
        ).exists():
            return  # Silent: prevents enumeration

        code = OTP.generate_code()
        RegistrationService._create_otp_safe(
            email, code, OTP.OTPType.PASSWORD_RESET,
        )
        send_otp_email_task.delay(
            email, code, OTP.OTPType.PASSWORD_RESET,
        )

    @staticmethod
    def verify_reset_otp(email, otp_code):
        """Verify reset OTP and issue a reset token."""
        email = email.lower().strip()
        RegistrationService.verify_otp(
            email, otp_code, OTP.OTPType.PASSWORD_RESET,
        )

        user = User.objects.get(email=email)
        # Invalidate old tokens
        PasswordResetToken.objects.filter(
            user=user, is_used=False,
        ).update(is_used=True)

        reset_token = PasswordResetToken.objects.create(user=user)
        return str(reset_token.token)

    @staticmethod
    @transaction.atomic
    def reset_password(reset_token_str, new_password):
        """Set new password using reset token."""
        try:
            token_obj = PasswordResetToken.objects.select_related(
                "user",
            ).get(token=reset_token_str)
        except PasswordResetToken.DoesNotExist:
            raise ValueError("Invalid or expired reset token.")

        if not token_obj.is_valid:
            raise ValueError("Invalid or expired reset token.")

        user = token_obj.user
        user.set_password(new_password)
        user.save(update_fields=["password"])

        token_obj.is_used = True
        token_obj.save(update_fields=["is_used"])

    @staticmethod
    def change_password(user, old_password, new_password):
        """Change password for authenticated user."""
        if not user.check_password(old_password):
            raise ValueError("Current password is incorrect.")
        user.set_password(new_password)
        user.save(update_fields=["password"])
