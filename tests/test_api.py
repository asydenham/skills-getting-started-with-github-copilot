"""
Test suite for Mergington High School Activities API

Uses AAA (Arrange-Act-Assert) pattern for clear test structure.
Tests cover GET, POST, DELETE endpoints and integration flows.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for each test with fresh app state"""
    return TestClient(app)


# ============================================================================
# GET /activities Tests
# ============================================================================

def test_get_activities_returns_all_activities(client):
    """
    Test that GET /activities returns all activities.
    
    Arrange: Create test client
    Act: GET /activities
    Assert: Status 200, response contains all 9 activities
    """
    # Arrange
    # (client fixture handles setup)
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    activities = response.json()
    assert len(activities) == 9
    expected_activities = [
        "Chess Club", "Programming Class", "Gym Class", 
        "Basketball Team", "Tennis Club", "Art Studio",
        "Drama Club", "Debate Team", "Science Club"
    ]
    for activity_name in expected_activities:
        assert activity_name in activities


def test_get_activities_structure(client):
    """
    Test that each activity has the expected structure.
    
    Arrange: Create test client
    Act: GET /activities
    Assert: Each activity has required fields (description, schedule, max_participants, participants)
    """
    # Arrange
    required_fields = ["description", "schedule", "max_participants", "participants"]
    
    # Act
    response = client.get("/activities")
    
    # Assert
    assert response.status_code == 200
    activities = response.json()
    for activity_name, activity_data in activities.items():
        for field in required_fields:
            assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"
        # Verify types
        assert isinstance(activity_data["description"], str)
        assert isinstance(activity_data["schedule"], str)
        assert isinstance(activity_data["max_participants"], int)
        assert isinstance(activity_data["participants"], list)


# ============================================================================
# POST /activities/{activity_name}/signup Tests
# ============================================================================

def test_signup_happy_path(client):
    """
    Test successful signup with valid activity and email.
    
    Arrange: Prepare valid activity name and new email
    Act: POST signup request
    Assert: Status 200, response confirms signup
    """
    # Arrange
    activity_name = "Chess Club"
    test_email = "newstudent@example.com"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Assert
    assert response.status_code == 200
    assert test_email in response.json()["message"]
    assert "Signed up" in response.json()["message"]


def test_signup_activity_not_found(client):
    """
    Test signup with non-existent activity.
    
    Arrange: Prepare fake activity name and valid email
    Act: POST signup request to fake activity
    Assert: Status 404, error message indicates activity not found
    """
    # Arrange
    fake_activity = "FakeActivity"
    test_email = "test@example.com"
    
    # Act
    response = client.post(
        f"/activities/{fake_activity}/signup",
        params={"email": test_email}
    )
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_signup_updates_state(client):
    """
    Test that participant appears in activity after signup.
    
    Arrange: Prepare new email and activity
    Act: POST signup, then GET activities
    Assert: Participant count increased, email in participants list
    """
    # Arrange
    activity_name = "Programming Class"
    test_email = "alice@example.com"
    
    # Get initial participant count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Act
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Assert
    assert signup_response.status_code == 200
    
    # Verify state changed
    updated_response = client.get("/activities")
    updated_activity = updated_response.json()[activity_name]
    assert len(updated_activity["participants"]) == initial_count + 1
    assert test_email in updated_activity["participants"]


def test_signup_duplicate_registration(client):
    """
    Test that duplicate signup is allowed (documents current behavior).
    
    Arrange: Prepare email already in activity
    Act: POST signup twice with same email
    Assert: Both requests return 200 (current behavior allows duplicates)
    """
    # Arrange
    activity_name = "Tennis Club"
    test_email = "duplicate@example.com"
    
    # Act - First signup
    response1 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Act - Second signup with same email
    response2 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Assert - Documents current behavior (allows duplicates)
    assert response1.status_code == 200
    assert response2.status_code == 200
    
    # Verify participant appears twice
    activities_response = client.get("/activities")
    participants = activities_response.json()[activity_name]["participants"]
    assert participants.count(test_email) == 2


# ============================================================================
# DELETE /activities/{activity_name}/participants/{email} Tests
# ============================================================================

def test_delete_participant_happy_path(client):
    """
    Test successful participant deletion.
    
    Arrange: Prepare existing participant
    Act: DELETE participant from activity
    Assert: Status 200, response confirms unregister
    """
    # Arrange
    activity_name = "Chess Club"
    existing_participant = "michael@mergington.edu"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{existing_participant}"
    )
    
    # Assert
    assert response.status_code == 200
    assert "Unregistered" in response.json()["message"]
    assert existing_participant in response.json()["message"]


def test_delete_activity_not_found(client):
    """
    Test delete from non-existent activity.
    
    Arrange: Prepare fake activity and valid email
    Act: DELETE from fake activity
    Assert: Status 404, error indicates activity not found
    """
    # Arrange
    fake_activity = "FakeActivity"
    test_email = "test@example.com"
    
    # Act
    response = client.delete(
        f"/activities/{fake_activity}/participants/{test_email}"
    )
    
    # Assert
    assert response.status_code == 404
    assert "Activity not found" in response.json()["detail"]


def test_delete_participant_not_found(client):
    """
    Test delete of non-existent participant from activity.
    
    Arrange: Prepare valid activity and email not in participants
    Act: DELETE non-existent participant
    Assert: Status 404, error indicates participant not found
    """
    # Arrange
    activity_name = "Gym Class"
    non_existent_email = "notregistered@example.com"
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/participants/{non_existent_email}"
    )
    
    # Assert
    assert response.status_code == 404
    assert "Participant not found" in response.json()["detail"]


def test_delete_updates_state(client):
    """
    Test that participant is removed from activity after delete.
    
    Arrange: Prepare existing participant and activity
    Act: DELETE participant, then GET activities
    Assert: Participant count decreased, email no longer in participants list
    """
    # Arrange
    activity_name = "Programming Class"
    participant_to_remove = "emma@mergington.edu"
    
    # Get initial count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Act
    delete_response = client.delete(
        f"/activities/{activity_name}/participants/{participant_to_remove}"
    )
    
    # Assert
    assert delete_response.status_code == 200
    
    # Verify state changed
    updated_response = client.get("/activities")
    updated_activity = updated_response.json()[activity_name]
    assert len(updated_activity["participants"]) == initial_count - 1
    assert participant_to_remove not in updated_activity["participants"]


# ============================================================================
# Integration Tests
# ============================================================================

def test_signup_then_unregister_flow(client):
    """
    Test full flow: signup then unregister.
    
    Arrange: Prepare new email and activity
    Act: POST signup, DELETE unregister
    Assert: Participant appears then disappears, final count correct
    """
    # Arrange
    activity_name = "Art Studio"
    test_email = "integration@example.com"
    
    # Get initial count
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Act - Signup
    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": test_email}
    )
    
    # Assert signup
    assert signup_response.status_code == 200
    after_signup = client.get("/activities")
    assert test_email in after_signup.json()[activity_name]["participants"]
    assert len(after_signup.json()[activity_name]["participants"]) == initial_count + 1
    
    # Act - Unregister
    delete_response = client.delete(
        f"/activities/{activity_name}/participants/{test_email}"
    )
    
    # Assert unregister
    assert delete_response.status_code == 200
    after_delete = client.get("/activities")
    assert test_email not in after_delete.json()[activity_name]["participants"]
    assert len(after_delete.json()[activity_name]["participants"]) == initial_count


def test_multiple_signups_state_tracking(client):
    """
    Test multiple signups with accurate state tracking.
    
    Arrange: Prepare 3 new emails and activity
    Act: POST signup for all three, GET activities
    Assert: All three in participants list, count accurate
    """
    # Arrange
    activity_name = "Drama Club"
    test_emails = ["student1@example.com", "student2@example.com", "student3@example.com"]
    
    initial_response = client.get("/activities")
    initial_count = len(initial_response.json()[activity_name]["participants"])
    
    # Act - Sign up all three students
    for email in test_emails:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
    
    # Assert - Verify all three are registered
    final_response = client.get("/activities")
    final_activity = final_response.json()[activity_name]
    
    for email in test_emails:
        assert email in final_activity["participants"]
    
    expected_count = initial_count + len(test_emails)
    assert len(final_activity["participants"]) == expected_count
