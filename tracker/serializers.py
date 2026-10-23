from django.utils import timezone
from rest_framework import serializers

from .models import Company, Interview, JobApplication, Reminder


class OwnedPrimaryKeyField(serializers.PrimaryKeyRelatedField):
    """Only allows references to objects owned by the requesting user.

    Without this, a user could attach their data to someone else's record by guessing IDs.
    """

    def get_queryset(self):
        request = self.context.get("request")
        queryset = super().get_queryset()
        if request is None or not request.user.is_authenticated:
            return queryset.none()
        return queryset.filter(owner=request.user)


class CompanySerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ("id", "name", "website", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be blank.")
        request = self.context["request"]
        duplicates = Company.objects.filter(owner=request.user, name__iexact=value)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError("You already have a company with this name.")
        return value


class JobApplicationSerializer(serializers.ModelSerializer):
    company = OwnedPrimaryKeyField(queryset=Company.objects.all())
    company_name = serializers.CharField(source="company.name", read_only=True)

    class Meta:
        model = JobApplication
        fields = (
            "id", "title", "company", "company_name", "status", "job_url",
            "applied_date", "notes", "created_at", "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate_applied_date(self, value):
        if value > timezone.localdate():
            raise serializers.ValidationError("Applied date cannot be in the future.")
        return value


class InterviewSerializer(serializers.ModelSerializer):
    application = OwnedPrimaryKeyField(queryset=JobApplication.objects.all())

    class Meta:
        model = Interview
        fields = ("id", "application", "scheduled_at", "interview_type", "feedback", "created_at")
        read_only_fields = ("id", "created_at")


class ReminderSerializer(serializers.ModelSerializer):
    application = OwnedPrimaryKeyField(queryset=JobApplication.objects.all())

    class Meta:
        model = Reminder
        fields = ("id", "application", "due_at", "reminder_type", "is_completed", "created_at")
        read_only_fields = ("id", "created_at")
