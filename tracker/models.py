from django.conf import settings
from django.db import models
from django.utils import timezone


class Company(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="companies")
    name = models.CharField(max_length=200)
    website = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "companies"
        constraints = [models.UniqueConstraint(fields=["owner", "name"], name="unique_company_per_owner")]

    def __str__(self):
        return self.name


class JobApplication(models.Model):
    class Status(models.TextChoices):
        APPLIED = "applied", "Applied"
        ASSESSMENT = "assessment", "Assessment"
        INTERVIEW = "interview", "Interview"
        OFFER = "offer", "Offer"
        REJECTED = "rejected", "Rejected"

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="applications")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="applications")
    title = models.CharField(max_length=200)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.APPLIED)
    job_url = models.URLField(blank=True)
    applied_date = models.DateField(default=timezone.localdate)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_date", "-id"]
        indexes = [models.Index(fields=["owner", "status"])]

    def __str__(self):
        return f"{self.title} @ {self.company}"


class Interview(models.Model):
    class Type(models.TextChoices):
        PHONE = "phone", "Phone screen"
        TECHNICAL = "technical", "Technical"
        HR = "hr", "HR"
        ONSITE = "onsite", "Onsite"
        OTHER = "other", "Other"

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="interviews")
    scheduled_at = models.DateTimeField()
    interview_type = models.CharField(max_length=20, choices=Type.choices, default=Type.OTHER)
    feedback = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["scheduled_at"]

    def __str__(self):
        return f"{self.get_interview_type_display()} for {self.application}"


class Reminder(models.Model):
    class Type(models.TextChoices):
        FOLLOW_UP = "follow_up", "Follow up"
        INTERVIEW_PREP = "interview_prep", "Interview prep"
        DEADLINE = "deadline", "Deadline"
        OTHER = "other", "Other"

    application = models.ForeignKey(JobApplication, on_delete=models.CASCADE, related_name="reminders")
    due_at = models.DateTimeField()
    reminder_type = models.CharField(max_length=20, choices=Type.choices, default=Type.FOLLOW_UP)
    is_completed = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at"]

    def __str__(self):
        return f"{self.get_reminder_type_display()} due {self.due_at:%Y-%m-%d %H:%M}"
