from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .filters import JobApplicationFilter
from .models import Company, Interview, JobApplication, Reminder
from .serializers import (
    CompanySerializer,
    InterviewSerializer,
    JobApplicationSerializer,
    ReminderSerializer,
)


class CompanyViewSet(viewsets.ModelViewSet):
    serializer_class = CompanySerializer
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Company.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class JobApplicationViewSet(viewsets.ModelViewSet):
    serializer_class = JobApplicationSerializer
    filterset_class = JobApplicationFilter
    search_fields = ["title", "company__name", "notes"]
    ordering_fields = ["applied_date", "created_at", "title", "status"]

    def get_queryset(self):
        return JobApplication.objects.filter(owner=self.request.user).select_related("company")

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class InterviewViewSet(viewsets.ModelViewSet):
    serializer_class = InterviewSerializer
    filterset_fields = ["application", "interview_type"]
    ordering_fields = ["scheduled_at", "created_at"]

    def get_queryset(self):
        return Interview.objects.filter(application__owner=self.request.user)


class ReminderViewSet(viewsets.ModelViewSet):
    serializer_class = ReminderSerializer
    filterset_fields = ["application", "reminder_type", "is_completed"]
    ordering_fields = ["due_at", "created_at"]

    def get_queryset(self):
        return Reminder.objects.filter(application__owner=self.request.user)

    @extend_schema(request=None)
    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark a reminder as completed."""
        reminder = self.get_object()
        reminder.is_completed = True
        reminder.save(update_fields=["is_completed"])
        return Response(self.get_serializer(reminder).data, status=status.HTTP_200_OK)


class DashboardStatsView(APIView):
    """Summary numbers for the logged-in user's job search."""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        now = timezone.now()
        applications = JobApplication.objects.filter(owner=request.user)
        by_status = {value: 0 for value in JobApplication.Status.values}
        for row in applications.values("status").annotate(total=Count("id")):
            by_status[row["status"]] = row["total"]
        reminders = Reminder.objects.filter(application__owner=request.user, is_completed=False)
        return Response(
            {
                "total_applications": applications.count(),
                "applications_by_status": by_status,
                "applications_last_30_days": applications.filter(
                    applied_date__gte=timezone.localdate() - timedelta(days=30)
                ).count(),
                "upcoming_interviews_next_7_days": Interview.objects.filter(
                    application__owner=request.user,
                    scheduled_at__gte=now,
                    scheduled_at__lte=now + timedelta(days=7),
                ).count(),
                "pending_reminders": reminders.count(),
                "overdue_reminders": reminders.filter(due_at__lt=now).count(),
            }
        )
