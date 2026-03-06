from django.contrib import admin
from .models import Unit, Mission


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ["unit_name", "unit_name_de", "created_at"]
    search_fields = ["unit_name", "unit_name_de"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]


@admin.register(Mission)
class MissionAdmin(admin.ModelAdmin):
    list_display = [
        "mission_name", "unit", "created_at",
    ]
    list_filter = ["unit"]
    search_fields = ["mission_name", "mission_name_de"]
    ordering = ["-created_at"]
    readonly_fields = ["id", "created_at", "updated_at"]
