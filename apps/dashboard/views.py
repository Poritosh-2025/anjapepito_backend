"""
Dashboard views with aggregated statistics.
FIX #11: Redis caching (120s TTL) eliminates repeated aggregation queries.
FIX #15: Uses User.Role enum.
"""
import calendar
from django.core.cache import cache
from django.db.models import Count
from django.db.models.functions import ExtractMonth
from django.utils import timezone
from rest_framework.views import APIView

from core.responses import success_response
from core.permissions import IsAdminUser
from core.mixins import ViewerContextMixin
from apps.authentication.models import User


class DashboardStatsView(ViewerContextMixin, APIView):
    """Dashboard summary statistics with Redis caching."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        today = timezone.now().date()
        cache_key = f"dashboard_stats_{today.isoformat()}"

        stats = cache.get(cache_key)
        if stats is None:
            total_users = User.objects.filter(
                role=User.Role.USER, is_verified=True,
            ).count()

            todays_new_users = User.objects.filter(
                role=User.Role.USER,
                is_verified=True,
                created_at__date=today,
            ).count()

            stats = {
                "total_users": total_users,
                "todays_new_users": todays_new_users,
            }
            cache.set(cache_key, stats, timeout=120)

        return success_response("Dashboard statistics retrieved.", {
            "viewer": self.get_viewer_data(request),
            **stats,
        })


class MonthlyGrowthView(ViewerContextMixin, APIView):
    """Monthly user growth with Redis caching."""
    permission_classes = [IsAdminUser]

    def get(self, request):
        year = request.query_params.get("year")
        if year:
            try:
                year = int(year)
            except (ValueError, TypeError):
                year = timezone.now().year
        else:
            year = timezone.now().year

        cache_key = f"monthly_growth_{year}"
        monthly_growth = cache.get(cache_key)

        if monthly_growth is None:
            monthly_data = (
                User.objects
                .filter(
                    role=User.Role.USER,
                    is_verified=True,
                    created_at__year=year,
                )
                .annotate(month=ExtractMonth("created_at"))
                .values("month")
                .annotate(new_users=Count("id"))
                .order_by("month")
            )

            month_counts = {
                row["month"]: row["new_users"] for row in monthly_data
            }

            monthly_growth = []
            for m in range(1, 13):
                monthly_growth.append({
                    "month": calendar.month_name[m],
                    "month_number": m,
                    "new_users": month_counts.get(m, 0),
                })

            cache.set(cache_key, monthly_growth, timeout=120)

        return success_response("Monthly growth data retrieved.", {
            "year": year,
            "viewer": self.get_viewer_data(request),
            "monthly_growth": monthly_growth,
        })
