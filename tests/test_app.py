import os
import sys
import copy
from fastapi.testclient import TestClient

# Ensure the application's src directory is importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

import app as app_module

client = TestClient(app_module.app)

# Keep an original copy of the activities state so we can reset before each test
_original_activities = copy.deepcopy(app_module.activities)

import pytest

@pytest.fixture(autouse=True)
def reset_activities():
    # Reset activities to original before each test
    app_module.activities = copy.deepcopy(_original_activities)
    yield


def test_root_redirect():
    response = client.get("/", follow_redirects=False)
    assert response.status_code in (307, 302)
    assert response.headers.get("location") == "/static/index.html"


def test_get_activities():
    response = client.get("/activities")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data


def test_signup_success():
    email = "alice@example.com"
    response = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response.status_code == 200
    assert f"Signed up {email}" in response.json()["message"]
    assert email in app_module.activities["Chess Club"]["participants"]


def test_signup_duplicate_returns_400():
    email = "bob@example.com"
    # First sign up should succeed
    response1 = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response1.status_code == 200

    # Second sign up should error
    response2 = client.post("/activities/Chess Club/signup", params={"email": email})
    assert response2.status_code == 400


def test_signup_unknown_activity_returns_404():
    response = client.post("/activities/Nonexistent/signup", params={"email": "x@x.com"})
    assert response.status_code == 404


def test_unregister_success():
    email = "carol@example.com"
    # Sign up then unregister
    client.post("/activities/Chess Club/signup", params={"email": email})
    response = client.delete("/activities/Chess Club/unregister", params={"email": email})
    assert response.status_code == 200
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_not_registered_returns_404():
    response = client.delete("/activities/Chess Club/unregister", params={"email": "not-registered@x.com"})
    assert response.status_code == 404


def test_unregister_unknown_activity_returns_404():
    response = client.delete("/activities/Nonexistent/unregister", params={"email": "x@x.com"})
    assert response.status_code == 404
