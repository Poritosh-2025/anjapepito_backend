"""
Business logic for Content Management.
Keeps views thin: validate → delegate to service → respond.
"""
import logging
from django.db import transaction
from django.db.models import Count

from .models import Unit, Mission

logger = logging.getLogger(__name__)


class CmsService:
    """Handles all CMS business operations."""

    # ── Unit Operations ──

    @staticmethod
    def get_units_queryset():
        """Returns annotated queryset with mission count."""
        return Unit.objects.annotate(
            number_of_missions=Count("missions"),
        ).order_by("-created_at")

    @staticmethod
    def get_unit_detail(unit_id):
        """Get a single unit with mission count annotation."""
        return Unit.objects.annotate(
            number_of_missions=Count("missions"),
        ).get(pk=unit_id)

    @staticmethod
    def create_unit(validated_data):
        """Create a new unit."""
        unit = Unit.objects.create(**validated_data)
        logger.info("Unit created: %s", unit.pk)
        return unit

    @staticmethod
    def update_unit(unit, validated_data):
        """Update unit fields."""
        for key, value in validated_data.items():
            setattr(unit, key, value)
        unit.save(update_fields=list(validated_data.keys()) + ["updated_at"])
        logger.info("Unit updated: %s", unit.pk)
        return unit

    @staticmethod
    @transaction.atomic
    def delete_unit(unit):
        """Delete unit and all its missions. Returns count of deleted missions."""
        mission_count = unit.missions.count()
        unit_id = str(unit.pk)
        unit.delete()  # CASCADE deletes missions; post_delete signal cleans files
        logger.info(
            "Unit %s deleted with %d missions", unit_id, mission_count,
        )
        return unit_id, mission_count

    # ── Mission Operations ──

    @staticmethod
    def get_missions_for_unit(unit):
        """Get all missions under a unit, ordered by creation."""
        return unit.missions.order_by("-created_at")

    @staticmethod
    def create_mission(unit, validated_data):
        """Create a mission under the given unit."""
        mission = Mission.objects.create(unit=unit, **validated_data)
        logger.info("Mission created: %s under unit %s", mission.pk, unit.pk)
        return mission

    @staticmethod
    def update_mission(mission, validated_data):
        """Update mission fields. File cleanup handled by model.save()."""
        for key, value in validated_data.items():
            setattr(mission, key, value)
        mission.save()  # save() override handles old file deletion
        logger.info("Mission updated: %s", mission.pk)
        return mission

    @staticmethod
    def delete_mission(mission):
        """Delete a single mission. post_delete signal cleans media files."""
        mission_id = str(mission.pk)
        unit_id = str(mission.unit_id)
        mission.delete()
        logger.info("Mission %s deleted from unit %s", mission_id, unit_id)
        return mission_id, unit_id
