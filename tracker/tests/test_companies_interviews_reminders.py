from datetime import timedelta

import pytest
from django.core import mail
from django.utils import timezone

from tracker.models import Company, Interview, JobApplication, Reminder
from tracker.tasks import send_due_reminders

pytestmark = pytest.mark.django_db


def test_company_crud_and_duplicate_name_rejected(client):
    assert client.post("/api/companies/", {"name": "Acme"}, format="json").status_code == 201
    dup = client.post("/api/companies/", {"name": "acme"}, format="json")
    assert dup.status_code == 400 and "name" in dup.data


def test_two_users_can_have_same_company_name(client, other_client):
    assert client.post("/api/companies/", {"name": "Acme"}, format="json").status_code == 201
    assert other_client.post("/api/companies/", {"name": "Acme"}, format="json").status_code == 201


def test_company_is_private_to_owner(other_client, company):
    assert other_client.get(f"/api/companies/{company.id}/").status_code == 404


def test_company_with_applications_cannot_be_deleted(client, application):
    # PROTECT on the foreign key stops accidental data loss; the API should not crash.
    from django.db.models import ProtectedError

    with pytest.raises(ProtectedError):
        client.delete(f"/api/companies/{application.company.id}/")


def test_create_interview(client, application):
    when = (timezone.now() + timedelta(days=2)).isoformat()
    res = client.post(
        "/api/interviews/",
        {"application": application.id, "scheduled_at": when, "interview_type": "technical"},
        format="json",
    )
    assert res.status_code == 201 and res.data["interview_type"] == "technical"


def test_interview_for_another_users_application_is_400(other_client, application):
    when = timezone.now().isoformat()
    res = other_client.post(
        "/api/interviews/", {"application": application.id, "scheduled_at": when}, format="json"
    )
    assert res.status_code == 400 and "application" in res.data


def test_interviews_hidden_from_other_users(other_client, application):
    interview = Interview.objects.create(application=application, scheduled_at=timezone.now())
    assert other_client.get("/api/interviews/").data["count"] == 0
    assert other_client.get(f"/api/interviews/{interview.id}/").status_code == 404


def test_reminder_complete_action(client, application):
    reminder = Reminder.objects.create(application=application, due_at=timezone.now())
    res = client.post(f"/api/reminders/{reminder.id}/complete/")
    assert res.status_code == 200 and res.data["is_completed"] is True


def test_other_user_cannot_complete_reminder(other_client, application):
    reminder = Reminder.objects.create(application=application, due_at=timezone.now())
    assert other_client.post(f"/api/reminders/{reminder.id}/complete/").status_code == 404
    reminder.refresh_from_db()
    assert reminder.is_completed is False


def test_filter_reminders_by_completion(client, application):
    Reminder.objects.create(application=application, due_at=timezone.now(), is_completed=True)
    Reminder.objects.create(application=application, due_at=timezone.now())
    assert client.get("/api/reminders/?is_completed=false").data["count"] == 1


def test_dashboard_stats(client, user, company, other_user):
    now = timezone.now()
    app1 = JobApplication.objects.create(owner=user, company=company, title="A", status="interview")
    JobApplication.objects.create(owner=user, company=company, title="B", status="applied")
    Interview.objects.create(application=app1, scheduled_at=now + timedelta(days=1))
    Interview.objects.create(application=app1, scheduled_at=now + timedelta(days=30))
    Reminder.objects.create(application=app1, due_at=now - timedelta(days=1))
    Reminder.objects.create(application=app1, due_at=now + timedelta(days=1))
    foreign_company = Company.objects.create(owner=other_user, name="X")
    JobApplication.objects.create(owner=other_user, company=foreign_company, title="Not mine")

    data = client.get("/api/dashboard/stats/").data
    assert data["total_applications"] == 2
    assert data["applications_by_status"]["interview"] == 1
    assert data["applications_by_status"]["offer"] == 0
    assert data["upcoming_interviews_next_7_days"] == 1
    assert data["pending_reminders"] == 2
    assert data["overdue_reminders"] == 1


def test_send_due_reminders_emails_once(settings, application):
    settings.EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
    due = Reminder.objects.create(application=application, due_at=timezone.now() - timedelta(minutes=1))
    Reminder.objects.create(application=application, due_at=timezone.now() + timedelta(days=1))
    Reminder.objects.create(application=application, due_at=timezone.now() - timedelta(days=1), is_completed=True)

    assert send_due_reminders() == 1
    assert len(mail.outbox) == 1 and application.owner.email in mail.outbox[0].to
    due.refresh_from_db()
    assert due.email_sent is True
    assert send_due_reminders() == 0
    assert len(mail.outbox) == 1
