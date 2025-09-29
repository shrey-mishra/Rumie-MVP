from fastapi.testclient import TestClient
from app.main import app
import uuid
import json

client = TestClient(app)

def test_get_chat_response():
    """Test chat response generation"""
    # First create a user
    unique_email = f"chat_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test chat response
    chat_request = {
        "message": "Hello, I need help organizing my tasks",
        "context": []
    }
    
    response = client.post(f"/v1/chat/response/{user_id}", json=chat_request)
    assert response.status_code == 200
    
    data = response.json()
    assert "response" in data
    assert "message_id" in data
    assert "timestamp" in data
    assert "confidence" in data
    assert "emotion" in data
    assert "personality_match" in data
    assert "mode_adapted" in data

def test_get_chat_context():
    """Test getting chat context"""
    # First create a user
    unique_email = f"context_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "creative",
        "personality_trait": "creative_thinker"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test getting context
    response = client.get(f"/v1/chat/context/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "chat_history" in data
    assert "last_updated" in data
    assert "session_id" in data

def test_set_chat_context():
    """Test setting chat context"""
    # First create a user
    unique_email = f"set_context_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "analytical_processor"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test setting context
    context_data = {
        "user_id": user_id,
        "chat_history": [
            {
                "role": "user",
                "content": "Hello",
                "timestamp": "2025-09-29T10:00:00Z",
                "message_id": "msg_001"
            },
            {
                "role": "assistant", 
                "content": "Hi there! How can I help you?",
                "timestamp": "2025-09-29T10:01:00Z",
                "message_id": "msg_002"
            }
        ],
        "last_updated": "2025-09-29T10:01:00Z",
        "session_id": f"chat:{user_id}"
    }
    
    response = client.post(f"/v1/chat/context/{user_id}", json=context_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "updated"
    assert "message_count" in data

def test_clear_chat_context():
    """Test clearing chat context"""
    # First create a user
    unique_email = f"clear_context_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "empathetic_listener"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test clearing context
    response = client.delete(f"/v1/chat/context/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "cleared"
    assert data["user_id"] == user_id

def test_get_chat_sessions():
    """Test getting chat sessions"""
    # First create a user
    unique_email = f"sessions_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test getting sessions
    response = client.get(f"/v1/chat/sessions/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "sessions" in data
    assert "total_sessions" in data

def test_chat_with_nonexistent_user():
    """Test chat with non-existent user"""
    response = client.post("/v1/chat/response/99999", json={
        "message": "Hello",
        "context": []
    })
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_chat_rate_limiting():
    """Test chat rate limiting"""
    # First create a user
    unique_email = f"rate_limit_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to exceed rate limit (20 requests per minute)
    responses = []
    for i in range(25):
        response = client.post(f"/v1/chat/response/{user_id}", json={
            "message": f"Test message {i}",
            "context": []
        })
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses or len([r for r in responses if r == 200]) <= 20
