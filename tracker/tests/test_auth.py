import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_register_creates_user_without_returning_password():
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "carol", "email": "carol@example.com", "password": "S3cure-pass-123"},
        format="json",
    )
    assert res.status_code == 201
    assert res.data["username"] == "carol"
    assert "password" not in res.data


def test_register_rejects_weak_password():
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "carol", "email": "carol@example.com", "password": "12345678"},
        format="json",
    )
    assert res.status_code == 400
    assert "non_field_errors" in res.data or "password" in res.data


def test_register_rejects_duplicate_email(user):
    res = APIClient().post(
        "/api/auth/register/",
        {"username": "other", "email": user.email.upper(), "password": "S3cure-pass-123"},
        format="json",
    )
    assert res.status_code == 400
    assert "email" in res.data


def test_login_returns_access_and_refresh_tokens(user):
    res = APIClient().post(
        "/api/auth/token/", {"username": "alice", "password": "S3cure-pass-123"}, format="json"
    )
    assert res.status_code == 200
    assert {"access", "refresh"} <= set(res.data)


def test_login_with_wrong_password_is_401(user):
    res = APIClient().post("/api/auth/token/", {"username": "alice", "password": "wrong"}, format="json")
    assert res.status_code == 401


def test_token_works_on_protected_endpoint_and_refresh_issues_new_access(user):
    api = APIClient()
    tokens = api.post(
        "/api/auth/token/", {"username": "alice", "password": "S3cure-pass-123"}, format="json"
    ).data
    api.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    assert api.get("/api/auth/me/").data["username"] == "alice"
    refreshed = APIClient().post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert refreshed.status_code == 200 and "access" in refreshed.data


@pytest.mark.parametrize(
    "path",
    ["/api/applications/", "/api/companies/", "/api/interviews/", "/api/reminders/", "/api/dashboard/stats/", "/api/auth/me/"],
)
def test_protected_endpoints_reject_anonymous_requests(path):
    assert APIClient().get(path).status_code == 401


def test_garbage_token_is_rejected():
    api = APIClient()
    api.credentials(HTTP_AUTHORIZATION="Bearer not-a-real-token")
    assert api.get("/api/applications/").status_code == 401
