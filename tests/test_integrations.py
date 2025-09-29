from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_get_google_workspace_mock():
    """Test Google Workspace mock integration"""
    # First create a user
    unique_email = f"google_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test Google Workspace integration
    response = client.get(f"/v1/integrations/google/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "gmail" in data
    assert "calendar" in data
    assert "last_sync" in data
    assert "status" in data
    assert data["status"] == "connected"
    
    # Check Gmail data structure
    gmail_data = data["gmail"]
    assert len(gmail_data) > 0
    assert "subject" in gmail_data[0]
    assert "sender" in gmail_data[0]
    assert "timestamp" in gmail_data[0]
    
    # Check Calendar data structure
    calendar_data = data["calendar"]
    assert len(calendar_data) > 0
    assert "title" in calendar_data[0]
    assert "start_time" in calendar_data[0]
    assert "attendees" in calendar_data[0]

def test_get_notion_mock():
    """Test Notion mock integration"""
    # First create a user
    unique_email = f"notion_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "creative",
        "personality_trait": "creative_thinker"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test Notion integration
    response = client.get(f"/v1/integrations/notion/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "tasks" in data
    assert "notes" in data
    assert "last_sync" in data
    assert "status" in data
    assert data["status"] == "connected"
    
    # Check Tasks data structure
    tasks_data = data["tasks"]
    assert len(tasks_data) > 0
    assert "title" in tasks_data[0]
    assert "description" in tasks_data[0]
    assert "due_date" in tasks_data[0]
    assert "priority" in tasks_data[0]
    assert "status" in tasks_data[0]
    
    # Check Notes data structure
    notes_data = data["notes"]
    assert len(notes_data) > 0
    assert "title" in notes_data[0]
    assert "content" in notes_data[0]
    assert "created_at" in notes_data[0]

def test_get_integrations_status():
    """Test integrations status endpoint"""
    # First create a user
    unique_email = f"status_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "analytical_processor"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test integrations status
    response = client.get(f"/v1/integrations/status/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "integrations" in data
    assert "overall_status" in data
    
    # Check integration statuses
    integrations = data["integrations"]
    assert "google_workspace" in integrations
    assert "notion" in integrations
    assert "slack" in integrations
    
    # Check Google Workspace status
    google_status = integrations["google_workspace"]
    assert "connected" in google_status
    assert "last_sync" in google_status
    assert "services" in google_status
    assert "status" in google_status

def test_integrations_with_nonexistent_user():
    """Test integrations with non-existent user"""
    # Test Google Workspace with non-existent user
    response = client.get("/v1/integrations/google/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test Notion with non-existent user
    response = client.get("/v1/integrations/notion/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test status with non-existent user
    response = client.get("/v1/integrations/status/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_integrations_rate_limiting():
    """Test integrations rate limiting"""
    # First create a user
    unique_email = f"rate_limit_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to exceed rate limit (10 requests per minute)
    responses = []
    for i in range(15):
        response = client.get(f"/v1/integrations/google/{user_id}")
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses or len([r for r in responses if r == 200]) <= 10
