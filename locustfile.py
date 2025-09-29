"""
Load testing for RumieAI Phase IV backend - Production Ready
Tests 200 users with JWT auth, Redis, and all endpoints
"""

from locust import HttpUser, task, between
import json
import random

class RumieAIUser(HttpUser):
    wait_time = between(1, 5)  # Simulate 100-200 users with higher frequency
    
    def on_start(self):
        """Authenticate user and get JWT token"""
        # Register a test user
        unique_email = f"load_test_{random.randint(1000, 9999)}@rumie.ai"
        register_data = {
            "email": unique_email,
            "password": "demo123",
            "mode_pref": "work",
            "personality_trait": "efficient_organizer"
        }
        
        response = self.client.post("/v1/auth/register", json=register_data)
        if response.status_code == 200:
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.user_id = 1  # Will be updated from auth/me
            self.user_email = unique_email
            
            # Get user info
            headers = {"Authorization": f"Bearer {self.access_token}"}
            user_response = self.client.get("/v1/auth/me", headers=headers)
            if user_response.status_code == 200:
                self.user_id = user_response.json()["id"]
        else:
            # Fallback to login
            login_response = self.client.post("/v1/auth/token", data={
                "username": "test@rumie.ai",
                "password": "demo123"
            })
            if login_response.status_code == 200:
                token_data = login_response.json()
                self.access_token = token_data["access_token"]
                self.user_id = 1
                self.user_email = "test@rumie.ai"
            else:
                self.access_token = None
                self.user_id = 1
                self.user_email = "default@rumie.ai"
    
    @task(3)
    def chat_response(self):
        """Test chat response endpoint (most frequent)"""
        if not self.access_token:
            return
            
        chat_messages = [
            "I need help organizing my daily tasks",
            "What's the best way to manage my time?",
            "Can you help me plan my week?",
            "I'm feeling overwhelmed with work",
            "How can I be more productive?",
            "What are some time management tips?",
            "Help me prioritize my tasks",
            "I need to focus better",
            "How can I improve my workflow?",
            "What's a good morning routine?"
        ]
        
        message = random.choice(chat_messages)
        chat_request = {
            "message": message,
            "context": []
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(
            f"/v1/chat/response/{self.user_id}",
            json=chat_request,
            headers=headers
        )
        
        if response.status_code not in [200, 429]:  # 429 is rate limited
            print(f"Chat response failed: {response.status_code} - {response.text}")
    
    @task(2)
    def productivity_timer(self):
        """Test productivity timer endpoints"""
        # Start timer
        start_response = self.client.post(
            f"/v1/productivity/timer/start",
            params={
                "user_id": self.user_id,
                "task_name": f"Load Test Task {random.randint(1, 100)}",
                "category": "testing"
            }
        )
        
        if start_response.status_code == 200:
            # Stop timer after a short delay
            import time
            time.sleep(0.1)
            
            stop_response = self.client.post(
                f"/v1/productivity/timer/stop",
                params={"user_id": self.user_id}
            )
    
    @task(1)
    def analytics_endpoints(self):
        """Test analytics endpoints"""
        analytics_endpoints = [
            f"/v1/analytics/youtube/{self.user_id}",
            f"/v1/analytics/twitch/{self.user_id}",
            f"/v1/analytics/cross-platform/{self.user_id}"
        ]
        
        endpoint = random.choice(analytics_endpoints)
        response = self.client.get(endpoint)
        
        if response.status_code not in [200, 429]:  # 429 is rate limited, which is expected
            print(f"Analytics endpoint failed: {endpoint} - {response.status_code}")
    
    @task(1)
    def campaign_endpoints(self):
        """Test campaign endpoints"""
        # Get campaign templates
        response = self.client.get("/v1/campaign/templates")
        
        if response.status_code == 200:
            # Run a small campaign
            campaign_request = {
                "campaign_name": f"Load Test Campaign {random.randint(1, 100)}",
                "message": "Test message for load testing",
                "recipients": [
                    {"email": "test@example.com", "name": "Test User"}
                ],
                "platform": "email",
                "personalization": False
            }
            
            campaign_response = self.client.post(
                f"/v1/campaign/run/{self.user_id}",
                json=campaign_request
            )
    
    @task(1)
    def voice_endpoints(self):
        """Test voice endpoints"""
        if not self.access_token:
            return
            
        # Test voice command
        voice_request = {
            "audio_transcript": f"Load test voice command {random.randint(1, 100)}"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(
            f"/v1/voice/command/{self.user_id}",
            json=voice_request,
            headers=headers
        )
    
    @task(1)
    def productivity_analytics(self):
        """Test productivity analytics"""
        analytics_endpoints = [
            f"/v1/productivity/saved-time/{self.user_id}",
            f"/v1/productivity/analytics/{self.user_id}",
            f"/v1/productivity/sessions/{self.user_id}"
        ]
        
        endpoint = random.choice(analytics_endpoints)
        response = self.client.get(endpoint)
    
    @task(1)
    def health_check(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        
        if response.status_code != 200:
            print(f"Health check failed: {response.status_code}")
    
    @task(1)
    def monitoring_endpoints(self):
        """Test monitoring endpoints"""
        if not self.access_token:
            return
            
        monitoring_endpoints = [
            "/v1/monitoring/redis-stats",
            "/v1/monitoring/system-health",
            "/v1/monitoring/performance-metrics",
            "/v1/monitoring/redis-optimization"
        ]
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        endpoint = random.choice(monitoring_endpoints)
        response = self.client.get(endpoint, headers=headers)
        
        if response.status_code not in [200, 429]:  # 429 is rate limited
            print(f"Monitoring endpoint failed: {endpoint} - {response.status_code}")
    
    @task(1)
    def mom_analyze(self):
        """Test MOM analysis endpoint"""
        if not self.access_token:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.get(f"/v1/mom/analyze/{self.user_id}?transcript=Test meeting transcript for load testing")
        
        if response.status_code not in [200, 429]:
            print(f"MOM analysis failed: {response.status_code}")
    
    @task(1)
    def campaign_run(self):
        """Test campaign execution endpoint"""
        if not self.access_token:
            return
            
        campaign_data = {
            "campaign_name": f"Load Test Campaign {random.randint(1, 100)}",
            "message": "Load testing campaign message",
            "recipients": [{"email": "test@example.com", "name": "Test User"}],
            "platform": "email",
            "personalization": True
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(f"/v1/campaign/run/{self.user_id}", 
                                  json=campaign_data, 
                                  headers=headers)
        
        if response.status_code not in [200, 429]:
            print(f"Campaign execution failed: {response.status_code}")
    
    @task(1)
    def voice_command(self):
        """Test voice command endpoint"""
        if not self.access_token:
            return
            
        voice_data = {
            "audio_transcript": f"Load test voice command {random.randint(1, 100)}"
        }
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post(f"/v1/voice/command/{self.user_id}", 
                                  json=voice_data, 
                                  headers=headers)
        
        if response.status_code not in [200, 429]:
            print(f"Voice command failed: {response.status_code}")
    
    @task(1)
    def productivity_insights(self):
        """Test productivity insights endpoint"""
        if not self.access_token:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.get(f"/v1/productivity/insights/{self.user_id}", headers=headers)
        
        if response.status_code not in [200, 429]:
            print(f"Productivity insights failed: {response.status_code}")
    
    @task(1)
    def analytics_endpoints(self):
        """Test analytics endpoints"""
        if not self.access_token:
            return
            
        analytics_endpoints = [
            f"/v1/analytics/youtube/{self.user_id}",
            f"/v1/analytics/twitch/{self.user_id}"
        ]
        
        headers = {"Authorization": f"Bearer {self.access_token}"}
        endpoint = random.choice(analytics_endpoints)
        response = self.client.get(endpoint, headers=headers)
        
        if response.status_code not in [200, 429]:
            print(f"Analytics endpoint failed: {endpoint} - {response.status_code}")
    
    @task(1)
    def auth_endpoints(self):
        """Test authentication endpoints"""
        auth_endpoints = [
            "/v1/auth/me",
            "/v1/auth/refresh"
        ]
        
        if self.access_token:
            headers = {"Authorization": f"Bearer {self.access_token}"}
            endpoint = random.choice(auth_endpoints)
            response = self.client.get(endpoint, headers=headers)
            
            if response.status_code not in [200, 429]:
                print(f"Auth endpoint failed: {endpoint} - {response.status_code}")
    
    @task(1)
    def redis_cleanup(self):
        """Test Redis cleanup endpoint"""
        if not self.access_token:
            return
            
        headers = {"Authorization": f"Bearer {self.access_token}"}
        response = self.client.post("/v1/monitoring/redis-cleanup", headers=headers)
        
        if response.status_code not in [200, 429]:
            print(f"Redis cleanup failed: {response.status_code}")

class RumieAISpikeUser(HttpUser):
    """Spike testing for sudden load increases"""
    wait_time = between(1, 3)  # Higher frequency for spike testing
    
    def on_start(self):
        self.user_id = random.randint(1, 10)  # Use existing users for spike testing
    
    @task(5)
    def chat_response_spike(self):
        """High frequency chat requests for spike testing"""
        chat_request = {
            "message": "Spike test message",
            "context": []
        }
        
        self.client.post(f"/v1/chat/response/{self.user_id}", json=chat_request)
    
    @task(2)
    def productivity_spike(self):
        """High frequency productivity requests"""
        self.client.get(f"/v1/productivity/analytics/{self.user_id}")
    
    @task(1)
    def analytics_spike(self):
        """High frequency analytics requests"""
        self.client.get(f"/v1/analytics/youtube/{self.user_id}")
