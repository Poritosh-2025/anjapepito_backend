from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path("stats/", views.DashboardStatsView.as_view(), name="stats"),
    path("monthly-growth/", views.MonthlyGrowthView.as_view(), name="monthly-growth"),
]
