"""
FIX #18: Delete orphaned profile picture files on re-upload.
"""
import logging
from django.db.models.signals import pre_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(pre_save, sender="authentication.User")
def delete_old_profile_picture(sender, instance, **kwargs):
    """Remove the old profile picture file when a new one is uploaded."""
    if not instance.pk:
        return

    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return

    old_pic = old_instance.profile_picture
    new_pic = instance.profile_picture

    if old_pic and old_pic != new_pic:
        try:
            old_pic.delete(save=False)
            logger.info(
                "Deleted old profile picture for user %s", instance.pk
            )
        except Exception as e:
            logger.warning(
                "Failed to delete old profile picture: %s", e
            )
