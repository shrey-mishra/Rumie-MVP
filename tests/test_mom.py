from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_analyze_meeting():
    """Test meeting analysis with MOM agent"""
    # First create a user
    unique_email = f"mom_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test meeting analysis
    meeting_data = {
        "transcript": "We discussed the project timeline and identified key milestones. John will prepare the technical specifications by Friday. Sarah will handle the client presentation. Next meeting scheduled for next week.",
        "meeting_title": "Project Planning Meeting",
        "participants": ["user@company.com", "john@company.com", "sarah@company.com"],
        "duration_minutes": 45
    }
    
    response = client.post(f"/v1/mom/analyze/{user_id}", json=meeting_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "summary" in data
    assert "key_points" in data
    assert "action_items" in data
    assert "next_steps" in data
    assert "participants" in data
    assert "duration" in data
    assert "confidence_score" in data
    
    # Check action items structure
    action_items = data["action_items"]
    assert len(action_items) > 0
    assert "task" in action_items[0]
    assert "owner" in action_items[0]
    assert "deadline" in action_items[0]
    assert "priority" in action_items[0]

def test_get_meeting_templates():
    """Test getting meeting templates"""
    # First create a user
    unique_email = f"templates_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "creative",
        "personality_trait": "creative_thinker"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test getting templates
    response = client.get(f"/v1/mom/templates/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "personality_trait" in data
    assert "mode_pref" in data
    assert "templates" in data
    
    # Check templates structure
    templates = data["templates"]
    assert len(templates) > 0
    assert "id" in templates[0]
    assert "name" in templates[0]
    assert "sections" in templates[0]
    assert "description" in templates[0]

def test_get_meeting_history():
    """Test getting meeting history"""
    # First create a user
    unique_email = f"history_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "analytical_processor"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test getting meeting history
    response = client.get(f"/v1/mom/history/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "meetings" in data
    assert "total_meetings" in data
    assert "last_updated" in data
    
    # Check meetings structure
    meetings = data["meetings"]
    assert len(meetings) > 0
    assert "id" in meetings[0]
    assert "title" in meetings[0]
    assert "date" in meetings[0]
    assert "duration" in meetings[0]
    assert "participants" in meetings[0]
    assert "action_items" in meetings[0]
    assert "status" in meetings[0]

def test_mom_with_nonexistent_user():
    """Test MOM endpoints with non-existent user"""
    # Test meeting analysis with non-existent user
    meeting_data = {
        "transcript": "Test transcript",
        "meeting_title": "Test Meeting",
        "participants": ["user@company.com"],
        "duration_minutes": 30
    }
    
    response = client.post("/v1/mom/analyze/99999", json=meeting_data)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test templates with non-existent user
    response = client.get("/v1/mom/templates/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test history with non-existent user
    response = client.get("/v1/mom/history/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_mom_rate_limiting():
    """Test MOM rate limiting"""
    # First create a user
    unique_email = f"rate_limit_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to exceed rate limit (5 requests per minute for analysis)
    responses = []
    meeting_data = {
        "transcript": "Test transcript",
        "meeting_title": "Test Meeting",
        "participants": ["user@company.com"],
        "duration_minutes": 30
    }
    
    for i in range(8):
        response = client.post(f"/v1/mom/analyze/{user_id}", json=meeting_data)
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses or len([r for r in responses if r == 200]) <= 5
