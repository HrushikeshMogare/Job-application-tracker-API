from datetime import timedelta

import pytest
from django.utils import timezone

from tracker.models import Company, JobApplication

pytestmark = pytest.mark.django_db


def payload(company, **extra):
    data = {"title": "Python Backend Developer", "company": company.id, "status": "applied"}
    data.update(extra)
    return data


def test_create_application_sets_owner_and_returns_201(client, user, company):
    res = client.post("/api/applications/", payload(company), format="json")
    assert res.status_code == 201
    assert res.data["company_name"] == "Example Technologies"
    assert JobApplication.objects.get(pk=res.data["id"]).owner == user


def test_status_defaults_to_applied(client, company):
    res = client.post("/api/applications/", {"title": "Dev", "company": company.id}, format="json")
    assert res.status_code == 201 and res.data["status"] == "applied"


def test_invalid_status_is_400(client, company):
    res = client.post("/api/applications/", payload(company, status="ghosted"), format="json")
    assert res.status_code == 400 and "status" in res.data


def test_blank_title_is_400(client, company):
    res = client.post("/api/applications/", payload(company, title="   "), format="json")
    assert res.status_code == 400 and "title" in res.data


def test_future_applied_date_is_400(client, company):
    future = (timezone.localdate() + timedelta(days=3)).isoformat()
    res = client.post("/api/applications/", payload(company, applied_date=future), format="json")
    assert res.status_code == 400 and "applied_date" in res.data


def test_invalid_job_url_is_400(client, company):
    res = client.post("/api/applications/", payload(company, job_url="not a url"), format="json")
    assert res.status_code == 400 and "job_url" in res.data


def test_cannot_use_another_users_company(client, other_user):
    foreign = Company.objects.create(owner=other_user, name="Foreign Corp")
    res = client.post("/api/applications/", payload(foreign), format="json")
    assert res.status_code == 400 and "company" in res.data


def test_update_and_status_change(client, application):
    res = client.patch(f"/api/applications/{application.id}/", {"status": "interview"}, format="json")
    assert res.status_code == 200 and res.data["status"] == "interview"


def test_delete_application(client, application):
    assert client.delete(f"/api/applications/{application.id}/").status_code == 204
    assert not JobApplication.objects.filter(pk=application.id).exists()


def test_user_only_sees_their_own_applications(client, other_client, application):
    assert client.get("/api/applications/").data["count"] == 1
    assert other_client.get("/api/applications/").data["count"] == 0


@pytest.mark.parametrize("method", ["get", "patch", "delete"])
def test_other_users_application_returns_404(other_client, application, method):
    res = getattr(other_client, method)(f"/api/applications/{application.id}/")
    assert res.status_code == 404
    assert JobApplication.objects.filter(pk=application.id).exists()


def test_filter_by_status_and_search(client, user, company):
    other_company = Company.objects.create(owner=user, name="Globex")
    JobApplication.objects.create(owner=user, company=company, title="Django Dev", status="offer")
    JobApplication.objects.create(owner=user, company=other_company, title="Data Analyst", status="applied")
    assert client.get("/api/applications/?status=offer").data["count"] == 1
    assert client.get("/api/applications/?search=globex").data["count"] == 1
    assert client.get("/api/applications/?search=django").data["count"] == 1
    assert client.get(f"/api/applications/?company={other_company.id}").data["count"] == 1


def test_filter_by_date_range(client, user, company):
    old = JobApplication.objects.create(owner=user, company=company, title="Old", applied_date="2024-01-10")
    JobApplication.objects.create(owner=user, company=company, title="New", applied_date="2024-06-10")
    res = client.get("/api/applications/?applied_before=2024-02-01")
    assert [r["id"] for r in res.data["results"]] == [old.id]


def test_ordering(client, user, company):
    for title in ["B role", "A role", "C role"]:
        JobApplication.objects.create(owner=user, company=company, title=title)
    res = client.get("/api/applications/?ordering=title")
    assert [r["title"] for r in res.data["results"]] == ["A role", "B role", "C role"]


def test_pagination(client, user, company):
    for i in range(12):
        JobApplication.objects.create(owner=user, company=company, title=f"Role {i}")
    first = client.get("/api/applications/").data
    assert first["count"] == 12 and len(first["results"]) == 10 and first["next"]
    assert len(client.get("/api/applications/?page=2").data["results"]) == 2
