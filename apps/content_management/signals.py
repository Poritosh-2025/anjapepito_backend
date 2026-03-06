"""
Post-delete signal: removes all 4 media files from disk when a Mission is deleted.
Works for both individual mission deletion and cascade deletion from Unit.
"""
import logging
from django.db.models.signals import post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


@receiver(post_delete, sender="content_management.Mission")
def delete_mission_media_files(sender, instance, **kwargs):
    """Remove video and thumbnail files from storage after mission deletion."""
    for field_name in instance.MEDIA_FIELDS:
        file_field = getattr(instance, field_name, None)
        if file_field:
            try:
                file_field.delete(save=False)
            except Exception as e:
                logger.warning(
                    "Failed to delete %s for mission %s: %s",
                    field_name, instance.pk, e,
                )
