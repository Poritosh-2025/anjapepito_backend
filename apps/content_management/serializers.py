"""
Serializers for Unit and Mission.
- UnitListSerializer: for paginated list (includes computed number_of_missions)
- UnitDetailSerializer: for single unit detail
- UnitWriteSerializer: for create/update
- MissionListSerializer: for paginated mission list under a unit
- MissionDetailSerializer: for single mission detail (includes unit_name)
- MissionCreateSerializer: all 10 fields required
- MissionUpdateSerializer: all fields optional (PATCH)
"""
from rest_framework import serializers
from .models import Unit, Mission
from .validators import validate_video_file, validate_image_file


# ━━━ UNIT SERIALIZERS ━━━

class UnitListSerializer(serializers.ModelSerializer):
    """For list view: includes computed mission count."""
    unit_id = serializers.UUIDField(source="id", read_only=True)
    number_of_missions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Unit
        fields = [
            "unit_id", "unit_name", "unit_name_de",
            "number_of_missions", "created_at",
        ]


class UnitDetailSerializer(serializers.ModelSerializer):
    """For detail view: same as list."""
    unit_id = serializers.UUIDField(source="id", read_only=True)
    number_of_missions = serializers.IntegerField(read_only=True)

    class Meta:
        model = Unit
        fields = [
            "unit_id", "unit_name", "unit_name_de",
            "number_of_missions", "created_at",
        ]


class UnitWriteSerializer(serializers.ModelSerializer):
    """For create and update. Both name fields required on create."""
    class Meta:
        model = Unit
        fields = ["unit_name", "unit_name_de"]

    def validate_unit_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_unit_name_de(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()


# ━━━ MISSION SERIALIZERS ━━━

class MissionListSerializer(serializers.ModelSerializer):
    """For list view: all 10 fields with absolute media URLs."""
    mission_id = serializers.UUIDField(source="id", read_only=True)

    class Meta:
        model = Mission
        fields = [
            "mission_id", "mission_name", "mission_name_de",
            "video", "video_thumbnail",
            "video_description", "video_description_de",
            "task_video", "task_thumbnail",
            "task", "task_de",
        ]


class MissionDetailSerializer(serializers.ModelSerializer):
    """For detail view: includes unit info for breadcrumbs."""
    mission_id = serializers.UUIDField(source="id", read_only=True)
    unit_id = serializers.UUIDField(source="unit.id", read_only=True)
    unit_name = serializers.CharField(source="unit.unit_name", read_only=True)

    class Meta:
        model = Mission
        fields = [
            "mission_id", "unit_id", "unit_name",
            "mission_name", "mission_name_de",
            "video", "video_thumbnail",
            "video_description", "video_description_de",
            "task_video", "task_thumbnail",
            "task", "task_de",
            "created_at",
        ]


class MissionCreateSerializer(serializers.ModelSerializer):
    """All 10 fields required on creation."""
    video = serializers.FileField(validators=[validate_video_file])
    video_thumbnail = serializers.ImageField(validators=[validate_image_file])
    task_video = serializers.FileField(validators=[validate_video_file])
    task_thumbnail = serializers.ImageField(validators=[validate_image_file])

    class Meta:
        model = Mission
        fields = [
            "mission_name", "mission_name_de",
            "video", "video_thumbnail",
            "video_description", "video_description_de",
            "task_video", "task_thumbnail",
            "task", "task_de",
        ]

    def validate_mission_name(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_mission_name_de(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_video_description(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_video_description_de(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_task(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()

    def validate_task_de(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip()


class MissionUpdateSerializer(serializers.ModelSerializer):
    """PATCH: all fields optional. File validators applied when present."""
    video = serializers.FileField(
        required=False, validators=[validate_video_file],
    )
    video_thumbnail = serializers.ImageField(
        required=False, validators=[validate_image_file],
    )
    task_video = serializers.FileField(
        required=False, validators=[validate_video_file],
    )
    task_thumbnail = serializers.ImageField(
        required=False, validators=[validate_image_file],
    )

    class Meta:
        model = Mission
        fields = [
            "mission_name", "mission_name_de",
            "video", "video_thumbnail",
            "video_description", "video_description_de",
            "task_video", "task_thumbnail",
            "task", "task_de",
        ]
        extra_kwargs = {f: {"required": False} for f in fields}

    def validate_mission_name(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip() if value else value

    def validate_mission_name_de(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value.strip() if value else value

    def validate_video_description(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_video_description_de(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_task(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value

    def validate_task_de(self, value):
        if value is not None and not value.strip():
            raise serializers.ValidationError("This field may not be blank.")
        return value
