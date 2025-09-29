from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_synthesize_speech():
    """Test voice synthesis (paid feature)"""
    # First create a user
    unique_email = f"voice_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Test voice synthesis
    voice_request = {
        "text": "Hello, this is a test message",
        "voice_type": "natural",
        "speed": 1.0,
        "language": "en-US"
    }
    
    response = client.post(f"/v1/voice/synthesize/{user_id}", json=voice_request)
    
    # Should either succeed (if user has access) or require payment
    assert response.status_code in [200, 402]
    
    if response.status_code == 200:
        data = response.json()
        assert "audio_url" in data
        assert "duration_seconds" in data
        assert "voice_type" in data
        assert "text_length" in data
        assert "processing_time_ms" in data
    else:
        assert "paid feature" in response.json()["detail"].lower()

def test_get_voice_sessions():
    """Test getting voice sessions"""
    # First create a user
    unique_email = f"voice_sessions_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Get voice sessions
    response = client.get(f"/v1/voice/sessions/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "sessions" in data
    assert "total_sessions" in data
    assert "limit" in data

def test_check_voice_access():
    """Test checking voice access status"""
    # First create a user
    unique_email = f"voice_access_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Check voice access
    response = client.get(f"/v1/voice/access/{user_id}")
    assert response.status_code == 200
    
    data = response.json()
    assert "user_id" in data
    assert "has_voice_access" in data
    assert "feature" in data
    assert "plan_required" in data

def test_get_available_voices():
    """Test getting available voice types"""
    response = client.get("/v1/voice/voices/available")
    assert response.status_code == 200
    
    data = response.json()
    assert "voices" in data
    assert "total_voices" in data
    assert "premium_voices" in data
    
    # Check voice structure
    voices = data["voices"]
    assert len(voices) > 0
    
    for voice in voices:
        assert "id" in voice
        assert "name" in voice
        assert "description" in voice
        assert "language" in voice
        assert "gender" in voice
        assert "premium" in voice

def test_voice_with_nonexistent_user():
    """Test voice endpoints with non-existent user"""
    # Test synthesis with non-existent user
    voice_request = {
        "text": "Test message",
        "voice_type": "natural",
        "speed": 1.0,
        "language": "en-US"
    }
    
    response = client.post("/v1/voice/synthesize/99999", json=voice_request)
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test sessions with non-existent user
    response = client.get("/v1/voice/sessions/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]
    
    # Test access check with non-existent user
    response = client.get("/v1/voice/access/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_delete_voice_session():
    """Test deleting a voice session"""
    # First create a user
    unique_email = f"delete_voice_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to delete non-existent session
    response = client.delete(f"/v1/voice/session/nonexistent_session", params={"user_id": user_id})
    assert response.status_code == 404
    assert "Voice session not found" in response.json()["detail"]

def test_voice_rate_limiting():
    """Test voice rate limiting"""
    # First create a user
    unique_email = f"voice_rate_test_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    assert user_response.status_code == 201
    user_id = user_response.json()["id"]
    
    # Try to exceed rate limit (5 requests per minute)
    voice_request = {
        "text": "Test message",
        "voice_type": "natural",
        "speed": 1.0,
        "language": "en-US"
    }
    
    responses = []
    for i in range(8):  # Try to exceed the 5/minute limit
        response = client.post(f"/v1/voice/synthesize/{user_id}", json=voice_request)
        responses.append(response.status_code)
    
    # At least one should be rate limited (429)
    assert 429 in responses or len([r for r in responses if r in [200, 402]]) <= 5
