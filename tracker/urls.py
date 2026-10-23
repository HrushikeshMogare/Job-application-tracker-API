from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    CompanyViewSet,
    DashboardStatsView,
    InterviewViewSet,
    JobApplicationViewSet,
    ReminderViewSet,
)

router = DefaultRouter()
router.register("companies", CompanyViewSet, basename="company")
router.register("applications", JobApplicationViewSet, basename="application")
router.register("interviews", InterviewViewSet, basename="interview")
router.register("reminders", ReminderViewSet, basename="reminder")

urlpatterns = [
    path("dashboard/stats/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("", include(router.urls)),
]
