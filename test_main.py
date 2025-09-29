from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_create_user():
    # Use a unique email for each test run
    unique_email = f"test_{uuid.uuid4().hex[:8]}@rumie.ai"
    response = client.post("/v1/users/", json={"email": unique_email, "mode_pref": "work", "personality_trait": "efficient_organizer"})
    assert response.status_code == 201
    assert response.json()["email"] == unique_email
    return response.json()["id"]  # Return user ID for other tests

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
    assert "version" in response.json()

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"
    assert "environment" in response.json()

def test_get_user():
    # First create a user
    user_id = test_create_user()
    
    # Then get the user
    response = client.get(f"/v1/users/{user_id}")
    assert response.status_code == 200
    assert "email" in response.json()
    assert "personality_trait" in response.json()

def test_ai_chat():
    # First create a user
    user_id = test_create_user()
    
    # Test AI chat
    response = client.post("/v1/ai/chat", json={
        "user_id": user_id,
        "message": "Hello, I need help with organizing my tasks"
    })
    assert response.status_code == 200
    assert "response" in response.json()
    assert "confidence" in response.json()
    assert "emotion" in response.json()

def test_rate_limiting():
    """Test that rate limiting works (this might fail in some environments)"""
    responses = []
    for i in range(15):  # Try to exceed the 10/minute limit
        response = client.get("/")
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses or len(responses) == 10  # Either rate limited or stopped at limit
