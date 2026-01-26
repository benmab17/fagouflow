import pytest
from rest_framework.test import APIClient

from accounts.models import User


@pytest.fixture()
def api_client():
    return APIClient()


@pytest.fixture()
def boss_user(db):
    return User.objects.create_user(
        email="boss@test.local",
        password="password",
        full_name="Boss",
        role="BOSS",
        site="BE",
    )