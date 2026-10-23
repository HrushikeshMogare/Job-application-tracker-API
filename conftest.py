import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from rest_framework.test import APIClient

from tracker.models import Company, JobApplication


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def make_user(db):
    def _make(username="alice", email=None, password="S3cure-pass-123"):
        return get_user_model().objects.create_user(
            username=username, email=email or f"{username}@example.com", password=password
        )

    return _make


@pytest.fixture
def user(make_user):
    return make_user("alice")


@pytest.fixture
def other_user(make_user):
    return make_user("bob")


def _client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def client(user):
    return _client_for(user)


@pytest.fixture
def other_client(other_user):
    return _client_for(other_user)


@pytest.fixture
def company(user):
    return Company.objects.create(owner=user, name="Example Technologies")


@pytest.fixture
def application(user, company):
    return JobApplication.objects.create(owner=user, company=company, title="Python Backend Developer")
