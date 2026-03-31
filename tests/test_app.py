import copy
import pytest
from fastapi.testclient import TestClient
from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database between tests."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


# ---------- GET / ----------

def test_root_redirects(client):
    # Arrange
    # (no setup needed)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert "/static/index.html" in response.headers["location"]


# ---------- GET /activities ----------

def test_get_activities_returns_all(client):
    # Arrange
    expected_keys = {"description", "schedule", "max_participants", "participants"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert len(data) > 0
    for name, details in data.items():
        assert expected_keys.issubset(details.keys()), f"{name} missing keys"


# ---------- POST /activities/{name}/signup ----------

def test_signup_success(client):
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert new_email in response.json()["message"]
    assert new_email in activities[activity_name]["participants"]


def test_signup_duplicate(client):
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert "already signed up" in response.json()["detail"].lower()


def test_signup_activity_not_found(client):
    # Arrange
    fake_activity = "Nonexistent Club"

    # Act
    response = client.post(
        f"/activities/{fake_activity}/signup",
        params={"email": "someone@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_signup_activity_full(client):
    # Arrange
    activity_name = "Chess Club"
    activities[activity_name]["max_participants"] = len(
        activities[activity_name]["participants"]
    )

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": "overflow@mergington.edu"},
    )

    # Assert
    assert response.status_code == 400
    assert "full" in response.json()["detail"].lower()


# ---------- DELETE /activities/{name}/signup ----------

def test_unregister_success(client):
    # Arrange
    activity_name = "Chess Club"
    email = activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]


def test_unregister_activity_not_found(client):
    # Arrange
    fake_activity = "Nonexistent Club"

    # Act
    response = client.delete(
        f"/activities/{fake_activity}/signup",
        params={"email": "someone@mergington.edu"},
    )

    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_unregister_not_participant(client):
    # Arrange
    activity_name = "Chess Club"
    non_member = "stranger@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": non_member},
    )

    # Assert
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()
