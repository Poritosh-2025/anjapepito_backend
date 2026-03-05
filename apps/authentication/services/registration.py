"""
Registration service handling user creation and OTP flows.
FIX #3: Catches IntegrityError on concurrent registration.
FIX #5: Celery dispatch via transaction.on_commit().
FIX #7: Anti-enumeration on resend_otp.
FIX #12: Catches IntegrityError on OTP creation race.
"""
import logging
from django.conf import settings
from django.db import transaction, IntegrityError
from django.utils import timezone

from apps.authentication.models import User, OTP
from apps.authentication.tasks import send_otp_email_task

logger = logging.getLogger(__name__)


class RegistrationService:
    """Handles user registration and OTP management."""

    @staticmethod
    @transaction.atomic
    def register_user(email, password, full_name, role=User.Role.USER):
        """
        Register a new user. Overwrites unverified duplicates.
        FIX #3: Catches IntegrityError from concurrent registration.
        """
        email = email.lower().strip()

        # Overwrite unverified duplicate
        User.objects.filter(email=email, is_verified=False).delete()

        # Check for verified duplicate
        if User.objects.filter(email=email, is_verified=True).exists():
            raise ValueError("A user with this email already exists.")

        try:
            user = User.objects.create_user(
                email=email,
                password=password,
                full_name=full_name,
                role=role,
                is_verified=False,
                has_access=True,
            )
        except IntegrityError:
            raise ValueError("A user with this email already exists.")

        # FIX #5: Dispatch Celery task AFTER transaction commits
        code = OTP.generate_code()
        RegistrationService._create_otp_safe(
            email, code, OTP.OTPType.REGISTER,
        )
        transaction.on_commit(
            lambda: send_otp_email_task.delay(
                email, code, OTP.OTPType.REGISTER,
            )
        )

        return user

    @staticmethod
    @transaction.atomic
    def register_superadmin(email, password, full_name):
        """Register superadmin (one-time setup)."""
        return RegistrationService.register_user(
            email=email,
            password=password,
            full_name=full_name,
            role=User.Role.SUPER_ADMIN,
        )

    @staticmethod
    def verify_otp(email, otp_code, otp_type):
        """Verify OTP and activate account if registration type."""
        email = email.lower().strip()

        try:
            otp = OTP.objects.get(email=email, otp_type=otp_type)
        except OTP.DoesNotExist:
            raise ValueError("No OTP found for this email.")

        if otp.is_expired:
            otp.delete()
            raise ValueError(
                "The OTP has expired. Please request a new one."
            )

        if otp.otp_code != otp_code:
            raise ValueError(
                "The OTP entered is incorrect or has expired."
            )

        otp.delete()

        if otp_type == OTP.OTPType.REGISTER:
            # FIX #17: Include updated_at in bulk update
            User.objects.filter(email=email).update(
                is_verified=True, updated_at=timezone.now(),
            )

        return True

    @staticmethod
    def resend_otp(email, otp_type):
        """
        Invalidate existing OTP and send a fresh one.
        FIX #7: Returns generic success to prevent email enumeration.
        """
        email = email.lower().strip()

        if otp_type == OTP.OTPType.REGISTER:
            if not User.objects.filter(
                email=email, is_verified=False,
            ).exists():
                return  # Silent: no error, no email
        elif otp_type == OTP.OTPType.PASSWORD_RESET:
            if not User.objects.filter(
                email=email, is_verified=True,
            ).exists():
                return  # Silent: no error, no email

        code = OTP.generate_code()
        RegistrationService._create_otp_safe(email, code, otp_type)
        send_otp_email_task.delay(email, code, otp_type)

    @staticmethod
    def _create_otp_safe(email, code, otp_type):
        """
        FIX #12: Delete-then-create with IntegrityError handling.
        """
        OTP.objects.filter(email=email, otp_type=otp_type).delete()
        try:
            OTP.objects.create(
                email=email, otp_code=code, otp_type=otp_type,
            )
        except IntegrityError:
            # Race condition: another request created first, overwrite
            OTP.objects.filter(
                email=email, otp_type=otp_type,
            ).delete()
            OTP.objects.create(
                email=email, otp_code=code, otp_type=otp_type,
            )
        logger.info("OTP created for %s (%s)", email, otp_type)
