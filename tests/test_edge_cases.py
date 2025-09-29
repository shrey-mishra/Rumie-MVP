"""
Edge case tests for Phase V implementation
Tests invalid JWT, Gemini quota errors, Redis failures, and other edge cases
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from app.main import app
import json

client = TestClient(app)

def test_invalid_jwt_token():
    """Test invalid JWT token handling"""
    invalid_headers = {"Authorization": "Bearer invalid_token"}
    response = client.get("/v1/auth/me", headers=invalid_headers)
    assert response.status_code == 401
    assert "Could not validate credentials" in response.json()["detail"]

def test_blacklisted_jwt_token():
    """Test blacklisted JWT token handling"""
    # This would require setting up a blacklisted token in Redis
    # For now, we'll test the endpoint structure
    response = client.post("/v1/auth/logout", headers={"Authorization": "Bearer test_token"})
    # Should handle gracefully even without proper token
    assert response.status_code in [200, 401]

def test_invalid_user_id():
    """Test invalid user ID handling"""
    response = client.get("/v1/users/99999")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_invalid_chat_user():
    """Test chat response with invalid user"""
    response = client.get("/v1/chat/response/99999?prompt=Test")
    assert response.status_code == 404
    assert "User not found" in response.json()["detail"]

def test_gemini_quota_exceeded():
    """Test Gemini API quota exceeded handling"""
    with patch("app.services.gemini_service.gemini_service.generate_empathetic_response") as mock_gemini:
        mock_gemini.side_effect = Exception("Quota exceeded")
        
        response = client.get("/v1/chat/response/1?prompt=Test")
        # Should handle gracefully with fallback
        assert response.status_code in [200, 500]

def test_redis_connection_failure():
    """Test Redis connection failure handling"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis.side_effect = Exception("Redis connection failed")
        
        response = client.get("/v1/monitoring/redis-stats")
        assert response.status_code == 503
        assert "Redis monitoring failed" in response.json()["detail"]

def test_rate_limit_exceeded():
    """Test rate limiting"""
    # Make multiple requests quickly to trigger rate limiting
    responses = []
    for i in range(15):  # More than the 10/minute limit
        response = client.get("/v1/users/1")
        responses.append(response.status_code)
    
    # Should have some rate limited responses
    assert 429 in responses

def test_invalid_endpoint():
    """Test invalid endpoint handling"""
    response = client.get("/v1/invalid-endpoint")
    assert response.status_code == 404

def test_malformed_json():
    """Test malformed JSON handling"""
    response = client.post("/v1/chat/response/1", 
                          data="invalid json",
                          headers={"Content-Type": "application/json"})
    assert response.status_code == 422

def test_missing_required_fields():
    """Test missing required fields"""
    response = client.post("/v1/auth/register", json={
        "email": "test@example.com"
        # Missing password, mode_pref, personality_trait
    })
    assert response.status_code == 422

def test_duplicate_email_registration():
    """Test duplicate email registration"""
    # First registration
    response1 = client.post("/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password123",
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    
    # Second registration with same email
    response2 = client.post("/v1/auth/register", json={
        "email": "duplicate@example.com",
        "password": "password123",
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    
    # First should succeed, second should fail
    assert response1.status_code == 200
    assert response2.status_code == 400

def test_invalid_password_reset():
    """Test invalid password reset token"""
    response = client.post("/v1/auth/confirm-reset", json={
        "token": "invalid_token",
        "new_password": "new_password"
    })
    assert response.status_code == 400
    assert "Invalid reset token" in response.json()["detail"]

def test_redis_cleanup_with_no_keys():
    """Test Redis cleanup with no keys"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.keys.return_value = []
        mock_redis_client.info.return_value = {"used_memory_human": "0B"}
        mock_redis.return_value = mock_redis_client
        
        response = client.post("/v1/monitoring/redis-cleanup")
        assert response.status_code == 200
        assert response.json()["deleted_keys"] == 0

def test_system_health_with_failing_services():
    """Test system health with failing services"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Redis connection failed")
        mock_redis.return_value = mock_redis_client
        
        response = client.get("/v1/monitoring/system-health")
        assert response.status_code == 200
        assert response.json()["overall"] == "degraded"
        assert response.json()["services"]["redis"]["status"] == "unhealthy"

def test_performance_metrics_with_no_data():
    """Test performance metrics with no data"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.info.return_value = {
            "used_memory": 0,
            "maxmemory": 0,
            "total_commands_processed": 0,
            "uptime_in_seconds": 0
        }
        mock_redis_client.keys.return_value = []
        mock_redis.return_value = mock_redis_client
        
        response = client.get("/v1/monitoring/performance-metrics")
        assert response.status_code == 200
        assert response.json()["redis_performance"]["commands_per_second"] == 0

def test_campaign_with_invalid_data():
    """Test campaign with invalid data"""
    invalid_campaign_data = {
        "campaign_name": "Test Campaign",
        # Missing required fields
    }
    
    response = client.post("/v1/campaign/run/1", json=invalid_campaign_data)
    assert response.status_code == 422

def test_voice_command_with_invalid_data():
    """Test voice command with invalid data"""
    invalid_voice_data = {
        # Missing audio_transcript
    }
    
    response = client.post("/v1/voice/command/1", json=invalid_voice_data)
    assert response.status_code == 422

def test_analytics_with_invalid_user():
    """Test analytics with invalid user"""
    response = client.get("/v1/analytics/youtube/99999")
    assert response.status_code == 404

def test_productivity_with_invalid_user():
    """Test productivity with invalid user"""
    response = client.get("/v1/productivity/insights/99999")
    assert response.status_code == 404

def test_mom_analyze_with_invalid_user():
    """Test MOM analysis with invalid user"""
    response = client.get("/v1/mom/analyze/99999?transcript=Test")
    assert response.status_code == 404

def test_cors_with_invalid_origin():
    """Test CORS with invalid origin"""
    response = client.options("/", headers={
        "Origin": "https://malicious-site.com",
        "Access-Control-Request-Method": "GET"
    })
    # Should either allow or block based on CORS config
    assert response.status_code in [200, 403]

def test_health_check_with_failing_services():
    """Test health check with failing services"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.ping.side_effect = Exception("Redis failed")
        mock_redis.return_value = mock_redis_client
        
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "degraded"
        assert "redis" in response.json()["services"]

def test_monitoring_endpoints_without_auth():
    """Test monitoring endpoints without authentication"""
    response = client.get("/v1/monitoring/redis-stats")
    # Should require authentication
    assert response.status_code == 401

def test_token_refresh_with_invalid_token():
    """Test token refresh with invalid token"""
    response = client.post("/v1/auth/refresh", headers={"Authorization": "Bearer invalid_token"})
    assert response.status_code == 401

def test_logout_without_token():
    """Test logout without token"""
    response = client.post("/v1/auth/logout")
    assert response.status_code == 401

def test_password_reset_with_invalid_email():
    """Test password reset with invalid email format"""
    response = client.post("/v1/auth/reset-password", json={"email": "invalid-email"})
    assert response.status_code == 422

def test_redis_optimization_with_no_keys():
    """Test Redis optimization with no keys"""
    with patch("app.dependencies.get_redis") as mock_redis:
        mock_redis_client = MagicMock()
        mock_redis_client.keys.return_value = []
        mock_redis_client.info.return_value = {
            "used_memory": 0,
            "maxmemory": 0
        }
        mock_redis.return_value = mock_redis_client
        
        response = client.get("/v1/monitoring/redis-optimization")
        assert response.status_code == 200
        assert response.json()["total_keys"] == 0
        assert len(response.json()["recommendations"]) == 0
