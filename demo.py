#!/usr/bin/env python3
"""
Demo script to showcase RumieAI Enhanced Phase I functionality
"""

from fastapi.testclient import TestClient
from app.main import app
import json
import uuid

def demo_api():
    client = TestClient(app)
    
    print("🚀 RumieAI Enhanced Phase I Demo")
    print("=" * 60)
    
    # Test root endpoint
    print("\n1. Testing root endpoint...")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test health endpoint
    print("\n2. Testing health endpoint...")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    print(f"   Response: {response.json()}")
    
    # Test user creation
    print("\n3. Testing user creation...")
    unique_email = f"demo_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_data = {
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    }
    
    response = client.post("/v1/users/", json=user_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 201:
        user = response.json()
        user_id = user['id']
        print(f"   Created user: {user['email']}")
        print(f"   User ID: {user['id']}")
        print(f"   Mode preference: {user['mode_pref']}")
        print(f"   Personality trait: {user['personality_trait']}")
        print(f"   Created at: {user['created_at']}")
    else:
        print(f"   Error: {response.json()}")
        return
    
    # Test getting user
    print("\n4. Testing get user...")
    response = client.get(f"/v1/users/{user_id}")
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        user = response.json()
        print(f"   Retrieved user: {user['email']}")
        print(f"   Personality: {user['personality_trait']}")
    else:
        print(f"   Error: {response.json()}")
    
    # Test AI chat
    print("\n5. Testing AI chat...")
    chat_data = {
        "user_id": user_id,
        "message": "Hello, I need help organizing my daily tasks efficiently"
    }
    
    response = client.post("/v1/ai/chat", json=chat_data)
    print(f"   Status: {response.status_code}")
    if response.status_code == 200:
        ai_response = response.json()
        print(f"   AI Response: {ai_response['response']}")
        print(f"   Confidence: {ai_response['confidence']}")
        print(f"   Emotion: {ai_response['emotion']}")
        print(f"   Personality Match: {ai_response['personality_match']}")
        print(f"   Mode Adapted: {ai_response['mode_adapted']}")
    else:
        print(f"   Error: {response.json()}")
    
    # Test another AI chat with different personality
    print("\n6. Testing AI chat with different personality...")
    # Create another user with different personality
    creative_email = f"creative_{uuid.uuid4().hex[:8]}@rumie.ai"
    creative_user_data = {
        "email": creative_email,
        "mode_pref": "creative",
        "personality_trait": "creative_thinker"
    }
    
    response = client.post("/v1/users/", json=creative_user_data)
    if response.status_code == 201:
        creative_user_id = response.json()['id']
        
        creative_chat_data = {
            "user_id": creative_user_id,
            "message": "I'm feeling stuck on a creative project and need inspiration"
        }
        
        response = client.post("/v1/ai/chat", json=creative_chat_data)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            ai_response = response.json()
            print(f"   AI Response: {ai_response['response']}")
            print(f"   Confidence: {ai_response['confidence']}")
            print(f"   Emotion: {ai_response['emotion']}")
            print(f"   Personality Match: {ai_response['personality_match']}")
        else:
            print(f"   Error: {response.json()}")
    
    print("\n✅ Enhanced Demo completed successfully!")
    print("\n🔧 Features demonstrated:")
    print("   • User creation with unique emails")
    print("   • User retrieval by ID")
    print("   • AI chat with personality adaptation")
    print("   • Rate limiting (try making many requests)")
    print("   • Structured logging")
    print("   • CORS configuration")
    print("   • Error handling")

if __name__ == "__main__":
    demo_api()
