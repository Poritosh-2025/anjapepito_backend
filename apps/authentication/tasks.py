"""Async tasks for OTP email delivery and cleanup."""
import logging
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def send_otp_email_task(self, email, otp_code, otp_type):
    """Send OTP email asynchronously with retry."""
    try:
        subject_map = {
            "register": "Verify Your Email - OTP Code",
            "password_reset": "Password Reset - OTP Code",
        }
        subject = subject_map.get(otp_type, "Your OTP Code")

        message = (
            f"Your verification code is: {otp_code}\n\n"
            f"This code expires in {settings.OTP_EXPIRY_MINUTES} minutes.\n"
            f"If you did not request this, please ignore this email."
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        logger.info("OTP email sent to %s", email)
    except Exception as exc:
        logger.error("Failed to send OTP to %s: %s", email, exc)
        raise self.retry(exc=exc)


@shared_task
def cleanup_expired_otps():
    """Delete OTPs older than expiry time."""
    from apps.authentication.models import OTP

    cutoff = timezone.now() - timedelta(
        minutes=settings.OTP_EXPIRY_MINUTES,
    )
    count, _ = OTP.objects.filter(created_at__lt=cutoff).delete()
    if count:
        logger.info("Cleaned up %d expired OTPs", count)


@shared_task
def cleanup_expired_reset_tokens():
    """Delete reset tokens older than 15 minutes."""
    from apps.authentication.models import PasswordResetToken

    cutoff = timezone.now() - timedelta(minutes=15)
    count, _ = PasswordResetToken.objects.filter(
        created_at__lt=cutoff,
    ).delete()
    if count:
        logger.info("Cleaned up %d expired reset tokens", count)


@shared_task
def cleanup_blacklisted_tokens():
    """Purge expired blacklisted JWT tokens."""
    try:
        from rest_framework_simplejwt.token_blacklist.models import (
            BlacklistedToken,
        )
        count, _ = BlacklistedToken.objects.filter(
            token__expires_at__lt=timezone.now(),
        ).delete()
        if count:
            logger.info("Purged %d expired blacklisted tokens", count)
    except Exception as e:
        logger.warning("Token cleanup skipped: %s", e)
