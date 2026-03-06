"""
Content Management API views.
Thin views: validate → delegate to service/queryset → wrap in envelope.
Auth: IsAdminUser (super_admin or staff_admin only).
"""
import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

from core.responses import success_response, error_response, created_response
from core.permissions import IsAdminUser
from core.pagination import StandardPagination
from core.mixins import PaginatedListMixin

from .models import Unit, Mission
from .serializers import (
    UnitListSerializer, UnitDetailSerializer, UnitWriteSerializer,
    MissionListSerializer, MissionDetailSerializer,
    MissionCreateSerializer, MissionUpdateSerializer,
)
from .services import CmsService

logger = logging.getLogger(__name__)


# ━━━━━━━━━━━━━━━━━━━━━━━━━
# UNIT VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━

class UnitListView(PaginatedListMixin, ListAPIView):
    """GET /cms/units/ — Paginated list of all units with mission count."""
    permission_classes = [IsAdminUser]
    serializer_class = UnitListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return CmsService.get_units_queryset()

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["message"] = "Unit list retrieved successfully."
        return response


class UnitCreateView(APIView):
    """POST /cms/units/create/ — Create a new unit."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = UnitWriteSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        unit = CmsService.create_unit(serializer.validated_data)

        # Re-fetch with annotation for response
        unit_with_count = CmsService.get_unit_detail(unit.pk)
        data = UnitDetailSerializer(unit_with_count).data
        return created_response("Unit created successfully.", data)


class UnitDetailView(APIView):
    """GET /cms/units/{unit_id}/ — Single unit detail."""
    permission_classes = [IsAdminUser]

    def get(self, request, unit_id):
        try:
            unit = CmsService.get_unit_detail(unit_id)
        except Unit.DoesNotExist:
            return error_response(
                "Unit not found.", status=status.HTTP_404_NOT_FOUND,
            )
        data = UnitDetailSerializer(unit).data
        return success_response("Unit detail retrieved.", data)


class UnitUpdateView(APIView):
    """PATCH /cms/units/{unit_id}/update/ — Partial update unit."""
    permission_classes = [IsAdminUser]

    def patch(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return error_response(
                "Unit not found.", status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UnitWriteSerializer(
            unit, data=request.data, partial=True,
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        CmsService.update_unit(unit, serializer.validated_data)

        # Re-fetch with annotation for response
        unit_with_count = CmsService.get_unit_detail(unit.pk)
        data = UnitDetailSerializer(unit_with_count).data
        return success_response("Unit updated successfully.", data)


class UnitDeleteView(APIView):
    """DELETE /cms/units/{unit_id}/delete/ — Delete unit + cascade missions."""
    permission_classes = [IsAdminUser]

    def delete(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return error_response(
                "Unit not found.", status=status.HTTP_404_NOT_FOUND,
            )

        deleted_id, mission_count = CmsService.delete_unit(unit)
        return success_response(
            "Unit and all associated missions have been permanently deleted.",
            {
                "deleted_unit_id": deleted_id,
                "missions_deleted": mission_count,
            },
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━
# MISSION VIEWS
# ━━━━━━━━━━━━━━━━━━━━━━━━━

class MissionListView(PaginatedListMixin, ListAPIView):
    """GET /cms/units/{unit_id}/missions/ — Paginated missions under a unit."""
    permission_classes = [IsAdminUser]
    serializer_class = MissionListSerializer
    pagination_class = StandardPagination

    def get_queryset(self):
        return Mission.objects.filter(
            unit_id=self.kwargs["unit_id"],
        ).order_by("-created_at")

    def list(self, request, *args, **kwargs):
        unit_id = self.kwargs["unit_id"]
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return error_response(
                "Unit not found.", status=status.HTTP_404_NOT_FOUND,
            )

        response = super().list(request, *args, **kwargs)
        page_data = response.data.get("data", {})
        page_data["unit_id"] = str(unit.pk)
        page_data["unit_name"] = unit.unit_name
        page_data["unit_name_de"] = unit.unit_name_de
        response.data["message"] = "Mission list retrieved successfully."
        return response


class MissionCreateView(APIView):
    """POST /cms/units/{unit_id}/missions/create/ — Create mission."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, unit_id):
        try:
            unit = Unit.objects.get(pk=unit_id)
        except Unit.DoesNotExist:
            return error_response(
                "Unit not found.", status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MissionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        mission = CmsService.create_mission(unit, serializer.validated_data)
        data = MissionDetailSerializer(
            mission, context={"request": request},
        ).data
        return created_response("Mission created successfully.", data)


class MissionDetailView(APIView):
    """GET /cms/missions/{mission_id}/ — Single mission detail."""
    permission_classes = [IsAdminUser]

    def get(self, request, mission_id):
        try:
            mission = Mission.objects.select_related("unit").get(
                pk=mission_id,
            )
        except Mission.DoesNotExist:
            return error_response(
                "Mission not found.", status=status.HTTP_404_NOT_FOUND,
            )

        data = MissionDetailSerializer(
            mission, context={"request": request},
        ).data
        return success_response("Mission detail retrieved.", data)


class MissionUpdateView(APIView):
    """PATCH /cms/missions/{mission_id}/update/ — Partial update mission."""
    permission_classes = [IsAdminUser]
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def patch(self, request, mission_id):
        try:
            mission = Mission.objects.select_related("unit").get(
                pk=mission_id,
            )
        except Mission.DoesNotExist:
            return error_response(
                "Mission not found.", status=status.HTTP_404_NOT_FOUND,
            )

        serializer = MissionUpdateSerializer(
            mission, data=request.data, partial=True,
        )
        if not serializer.is_valid():
            return error_response("Validation failed.", serializer.errors)

        CmsService.update_mission(mission, serializer.validated_data)

        # Re-fetch with select_related for clean response with URLs
        mission = Mission.objects.select_related("unit").get(pk=mission.pk)
        data = MissionDetailSerializer(
            mission, context={"request": request},
        ).data
        return success_response("Mission updated successfully.", data)


class MissionDeleteView(APIView):
    """DELETE /cms/missions/{mission_id}/delete/ — Delete single mission."""
    permission_classes = [IsAdminUser]

    def delete(self, request, mission_id):
        try:
            mission = Mission.objects.get(pk=mission_id)
        except Mission.DoesNotExist:
            return error_response(
                "Mission not found.", status=status.HTTP_404_NOT_FOUND,
            )

        deleted_id, unit_id = CmsService.delete_mission(mission)
        return success_response(
            "Mission has been permanently deleted.",
            {
                "deleted_mission_id": deleted_id,
                "unit_id": unit_id,
            },
        )
