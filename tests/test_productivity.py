from fastapi.testclient import TestClient
from app.main import app
import uuid
import time

client = TestClient(app)

def test_start_productivity_timer():
    """Test starting a productivity timer"""
    # First create a user
    unique_email = f"timer_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Start timer
    response = client.post(f"/v1/productivity/timer/start", params={
        "user_id": user_id,
        "task_name": "Test Task",
        "category": "development"
    })
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "timer_started"
    assert data["task_name"] == "Test Task"
    assert data["category"] == "development"
    assert "start_time" in data

def test_stop_productivity_timer():
    """Test stopping a productivity timer"""
    # First create a user
    unique_email = f"timer_stop_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Start timer
    start_response = client.post(f"/v1/productivity/timer/start", params={
        "user_id": user_id,
        "task_name": "Test Task",
        "category": "development"
    })
    assert start_response.status_code == 200
    
    # Wait a moment
    time.sleep(1)
    
    # Stop timer
    response = client.post(f"/v1/productivity/timer/stop", params={"user_id": user_id})
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "timer_stopped"
    assert data["duration_minutes"] >= 0
    assert data["task_name"] == "Test Task"

def test_get_timer_status():
    """Test getting timer status"""
    # First create a user
    unique_email = f"status_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Get status (no active timer)
    response = client.get(f"/v1/productivity/timer/status/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["user_id"] == user_id
    assert data["has_active_timer"] == False
    assert data["current_session"] is None

def test_get_productivity_analytics():
    """Test getting productivity analytics"""
    # First create a user
    unique_email = f"analytics_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Get analytics
    response = client.get(f"/v1/productivity/analytics/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "total_focus_time" in data
    assert "sessions_completed" in data
    assert "average_session_duration" in data
    assert "most_productive_category" in data
    assert "daily_breakdown" in data
    assert "weekly_trend" in data

def test_get_user_sessions():
    """Test getting user productivity sessions"""
    # First create a user
    unique_email = f"sessions_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Get sessions
    response = client.get(f"/v1/productivity/sessions/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "sessions" in data
    assert "total_sessions" in data
    assert "limit" in data

def test_productivity_with_nonexistent_user():
    """Test productivity endpoints with non-existent user"""
    # Test timer start with non-existent user
    response = client.post("/v1/productivity/timer/start", params={
        "user_id": 99999,
        "task_name": "Test Task",
        "category": "development"
    })
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test analytics with non-existent user
    response = client.get("/v1/productivity/analytics/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_timer_already_active():
    """Test starting timer when one is already active"""
    # First create a user
    unique_email = f"active_timer_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Start first timer
    response1 = client.post(f"/v1/productivity/timer/start", params={
        "user_id": user_id,
        "task_name": "First Task",
        "category": "development"
    })
    assert response1.status_code == 200
    
    # Try to start second timer (should fail)
    response2 = client.post(f"/v1/productivity/timer/start", params={
        "user_id": user_id,
        "task_name": "Second Task",
        "category": "development"
    })
    assert response2.status_code == 400
    assert "already has an active timer" in response2.json()["detail"]

def test_stop_timer_without_active_timer():
    """Test stopping timer when none is active"""
    # First create a user
    unique_email = f"no_timer_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to stop timer (should fail)
    response = client.post(f"/v1/productivity/timer/stop", params={"user_id": user_id})
    assert response.status_code == 400
    assert "No active timer session" in response.json()["detail"]
