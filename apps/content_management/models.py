"""
Content Management models: Unit (parent) and Mission (child).

Design decisions:
- UUID primary keys for external exposure safety
- number_of_missions is computed via annotation, not stored
- FileField for video (no size validation at DB level — done in serializer)
- ImageField for thumbnails (built-in image validation)
- CASCADE delete: deleting a Unit removes all its Missions
- UUID-based file naming prevents upload collisions
"""

import uuid
from django.db import models
from core.models import TimeStampedModel


def upload_video(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f"cms/videos/{uuid.uuid4().hex}.{ext}"


def upload_thumbnail(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f"cms/thumbnails/{uuid.uuid4().hex}.{ext}"


def upload_task_video(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f"cms/task_videos/{uuid.uuid4().hex}.{ext}"


def upload_task_thumbnail(instance, filename):
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return f"cms/task_thumbs/{uuid.uuid4().hex}.{ext}"


class Unit(TimeStampedModel):
    """
    Top-level content grouping (like a course or chapter).
    Has bilingual name fields (English + German).
    number_of_missions is always computed dynamically via annotation.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit_name = models.CharField(max_length=255)
    unit_name_de = models.CharField(max_length=255)

    class Meta:
        db_table = "cms_units"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["-created_at"], name="idx_unit_created"),
        ]

    def __str__(self):
        return f"{self.unit_name} / {self.unit_name_de}"


class Mission(TimeStampedModel):
    """
    Content item inside a Unit. 10 fields: 6 text (bilingual) + 4 media.
    On delete, post_delete signal removes media files from storage.
    On update, save() override removes replaced media files.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name="missions",
    )

    # Bilingual text fields
    mission_name = models.CharField(max_length=255)
    mission_name_de = models.CharField(max_length=255)
    video_description = models.TextField()
    video_description_de = models.TextField()
    task = models.TextField()
    task_de = models.TextField()

    # Media fields
    video = models.FileField(upload_to=upload_video)
    video_thumbnail = models.ImageField(upload_to=upload_thumbnail)
    task_video = models.FileField(upload_to=upload_task_video)
    task_thumbnail = models.ImageField(upload_to=upload_task_thumbnail)

    MEDIA_FIELDS = ["video", "video_thumbnail", "task_video", "task_thumbnail"]

    class Meta:
        db_table = "cms_missions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["unit", "-created_at"],
                name="idx_mission_unit",
            ),
        ]

    def __str__(self):
        return f"{self.mission_name} ({self.unit.unit_name})"

    def save(self, *args, **kwargs):
        """On update: delete old media files when replaced with new ones."""
        if not self._state.adding:
            try:
                old = Mission.objects.get(pk=self.pk)
                for field_name in self.MEDIA_FIELDS:
                    old_file = getattr(old, field_name)
                    new_file = getattr(self, field_name)
                    if old_file and old_file != new_file:
                        old_file.delete(save=False)
            except Mission.DoesNotExist:
                pass
        super().save(*args, **kwargs)
