from django.urls import path
from . import views

app_name = "content_management"

urlpatterns = [
    # Unit endpoints
    path("units/", views.UnitListView.as_view(), name="unit-list"),
    path("units/create/", views.UnitCreateView.as_view(), name="unit-create"),
    path("units/<uuid:unit_id>/", views.UnitDetailView.as_view(), name="unit-detail"),
    path("units/<uuid:unit_id>/update/", views.UnitUpdateView.as_view(), name="unit-update"),
    path("units/<uuid:unit_id>/delete/", views.UnitDeleteView.as_view(), name="unit-delete"),

    # Mission endpoints (nested under unit)
    path("units/<uuid:unit_id>/missions/", views.MissionListView.as_view(), name="mission-list"),
    path("units/<uuid:unit_id>/missions/create/", views.MissionCreateView.as_view(), name="mission-create"),

    # Mission endpoints (direct by mission_id)
    path("missions/<uuid:mission_id>/", views.MissionDetailView.as_view(), name="mission-detail"),
    path("missions/<uuid:mission_id>/update/", views.MissionUpdateView.as_view(), name="mission-update"),
    path("missions/<uuid:mission_id>/delete/", views.MissionDeleteView.as_view(), name="mission-delete"),
]
