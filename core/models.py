"""Abstract base models for consistency across all apps."""
import uuid
from django.db import models


class TimeStampedModel(models.Model):
    """Provides created_at / updated_at timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ["-created_at"]


class UUIDModel(models.Model):
    """Provides a UUID primary key."""
    id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )

    class Meta:
        abstract = True
