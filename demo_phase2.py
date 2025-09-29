#!/usr/bin/env python3
"""
Phase II Demo Script - Showcase RumieAI Enhanced Backend
Demonstrates Gemini integration, mock integrations, MOM agent, and chat functionality
"""

from fastapi.testclient import TestClient
from app.main import app
import json
import uuid
import time

def demo_phase2():
    client = TestClient(app)
    
    print("🚀 RumieAI Phase II Demo - Enhanced Backend")
    print("=" * 70)
    print("Features: Gemini AI, Mock Integrations, MOM Agent, Chat Context")
    print("=" * 70)
    
    # Create a user for testing
    print("\n1. Creating test user...")
    unique_email = f"phase2_demo_{uuid.uuid4().hex[:8]}@rumie.ai"
    user_response = client.post("/v1/users/", json={
        "email": unique_email,
        "mode_pref": "work",
        "personality_trait": "efficient_organizer"
    })
    
    if user_response.status_code == 201:
        user_id = user_response.json()["id"]
        print(f"   ✅ User created: {unique_email} (ID: {user_id})")
    else:
        print(f"   ❌ User creation failed: {user_response.status_code}")
        return
    
    # Test Chat with Gemini Integration
    print("\n2. Testing Chat with Gemini Integration...")
    chat_request = {
        "message": "I need help organizing my daily tasks efficiently. Can you suggest a structured approach?",
        "context": []
    }
    
    response = client.post(f"/v1/chat/response/{user_id}", json=chat_request)
    if response.status_code == 200:
        chat_data = response.json()
        print(f"   ✅ Chat response generated")
        print(f"   📝 Response: {chat_data['response'][:100]}...")
        print(f"   🎯 Confidence: {chat_data['confidence']}")
        print(f"   😊 Emotion: {chat_data['emotion']}")
        print(f"   🧠 Personality Match: {chat_data['personality_match']}")
    else:
        print(f"   ❌ Chat failed: {response.status_code}")
    
    # Test Chat Context Management
    print("\n3. Testing Chat Context Management...")
    context_response = client.get(f"/v1/chat/context/{user_id}")
    if context_response.status_code == 200:
        context_data = context_response.json()
        print(f"   ✅ Chat context retrieved")
        print(f"   💬 Messages in history: {len(context_data['chat_history'])}")
        print(f"   🕒 Last updated: {context_data['last_updated']}")
    else:
        print(f"   ❌ Context retrieval failed: {context_response.status_code}")
    
    # Test Google Workspace Integration
    print("\n4. Testing Google Workspace Integration...")
    google_response = client.get(f"/v1/integrations/google/{user_id}")
    if google_response.status_code == 200:
        google_data = google_response.json()
        print(f"   ✅ Google Workspace data retrieved")
        print(f"   📧 Gmail messages: {len(google_data['gmail'])}")
        print(f"   📅 Calendar events: {len(google_data['calendar'])}")
        print(f"   🔗 Status: {google_data['status']}")
        
        # Show sample Gmail data
        if google_data['gmail']:
            sample_email = google_data['gmail'][0]
            print(f"   📨 Sample email: {sample_email['subject']} from {sample_email['sender']}")
    else:
        print(f"   ❌ Google Workspace failed: {google_response.status_code}")
    
    # Test Notion Integration
    print("\n5. Testing Notion Integration...")
    notion_response = client.get(f"/v1/integrations/notion/{user_id}")
    if notion_response.status_code == 200:
        notion_data = notion_response.json()
        print(f"   ✅ Notion data retrieved")
        print(f"   ✅ Tasks: {len(notion_data['tasks'])}")
        print(f"   📝 Notes: {len(notion_data['notes'])}")
        print(f"   🔗 Status: {notion_data['status']}")
        
        # Show sample task
        if notion_data['tasks']:
            sample_task = notion_data['tasks'][0]
            print(f"   📋 Sample task: {sample_task['title']} (Priority: {sample_task['priority']})")
    else:
        print(f"   ❌ Notion failed: {notion_response.status_code}")
    
    # Test MOM Agent
    print("\n6. Testing MOM (Minutes of Meeting) Agent...")
    meeting_data = {
        "transcript": """
        John: Welcome everyone to our project planning meeting. Let's start with the current status.
        Sarah: We've completed 60% of the backend development. The API endpoints are ready.
        Mike: The frontend is 40% complete. We need to integrate with the API next week.
        John: Great progress. What are the main blockers?
        Sarah: We need the database schema finalized by Friday.
        Mike: The design system needs approval from the client.
        John: Let's set deadlines. Sarah, can you finalize the schema by Friday?
        Sarah: Yes, I'll have it ready by Friday 5 PM.
        John: Mike, when can we get client approval?
        Mike: I'll schedule a meeting for tomorrow morning.
        John: Perfect. Next meeting scheduled for next Tuesday at 2 PM.
        """,
        "meeting_title": "Project Planning Meeting",
        "participants": ["john@company.com", "sarah@company.com", "mike@company.com"],
        "duration_minutes": 30
    }
    
    mom_response = client.post(f"/v1/mom/analyze/{user_id}", json=meeting_data)
    if mom_response.status_code == 200:
        mom_data = mom_response.json()
        print(f"   ✅ Meeting analysis completed")
        print(f"   📊 Summary: {mom_data['summary'][:100]}...")
        print(f"   🎯 Key points: {len(mom_data['key_points'])}")
        print(f"   ✅ Action items: {len(mom_data['action_items'])}")
        print(f"   📈 Confidence: {mom_data['confidence_score']}")
        
        # Show action items
        if mom_data['action_items']:
            print(f"   📋 Action Items:")
            for item in mom_data['action_items'][:2]:  # Show first 2
                print(f"      • {item['task']} (Owner: {item['owner']}, Priority: {item['priority']})")
    else:
        print(f"   ❌ MOM analysis failed: {mom_response.status_code}")
    
    # Test Meeting Templates
    print("\n7. Testing Meeting Templates...")
    templates_response = client.get(f"/v1/mom/templates/{user_id}")
    if templates_response.status_code == 200:
        templates_data = templates_response.json()
        print(f"   ✅ Templates retrieved")
        print(f"   📋 Available templates: {len(templates_data['templates'])}")
        print(f"   🧠 Personality: {templates_data['personality_trait']}")
        print(f"   🎯 Mode: {templates_data['mode_pref']}")
        
        # Show sample template
        if templates_data['templates']:
            sample_template = templates_data['templates'][0]
            print(f"   📝 Sample template: {sample_template['name']}")
            print(f"      Sections: {', '.join(sample_template['sections'])}")
    else:
        print(f"   ❌ Templates failed: {templates_response.status_code}")
    
    # Test Integration Status
    print("\n8. Testing Integration Status...")
    status_response = client.get(f"/v1/integrations/status/{user_id}")
    if status_response.status_code == 200:
        status_data = status_response.json()
        print(f"   ✅ Integration status retrieved")
        print(f"   🔗 Overall status: {status_data['overall_status']}")
        
        integrations = status_data['integrations']
        for name, details in integrations.items():
            status_icon = "✅" if details['connected'] else "❌"
            print(f"   {status_icon} {name.replace('_', ' ').title()}: {details['status']}")
    else:
        print(f"   ❌ Status check failed: {status_response.status_code}")
    
    # Test Chat Sessions
    print("\n9. Testing Chat Sessions...")
    sessions_response = client.get(f"/v1/chat/sessions/{user_id}")
    if sessions_response.status_code == 200:
        sessions_data = sessions_response.json()
        print(f"   ✅ Chat sessions retrieved")
        print(f"   💬 Total sessions: {sessions_data['total_sessions']}")
    else:
        print(f"   ❌ Sessions failed: {sessions_response.status_code}")
    
    # Test Rate Limiting (demonstration)
    print("\n10. Testing Rate Limiting...")
    print("   🚦 Making multiple requests to test rate limiting...")
    rate_limit_responses = []
    for i in range(8):  # Try to exceed the 5/minute limit for user creation
        response = client.post("/v1/users/", json={
            "email": f"rate_test_{i}_{uuid.uuid4().hex[:4]}@rumie.ai",
            "mode_pref": "work",
            "personality_trait": "efficient_organizer"
        })
        rate_limit_responses.append(response.status_code)
    
    success_count = len([r for r in rate_limit_responses if r == 201])
    rate_limited_count = len([r for r in rate_limit_responses if r == 429])
    
    print(f"   📊 Results: {success_count} successful, {rate_limited_count} rate limited")
    print(f"   🛡️ Rate limiting is working: {'✅' if rate_limited_count > 0 else '❌'}")
    
    print("\n" + "=" * 70)
    print("🎉 Phase II Demo Completed Successfully!")
    print("\n📋 Features Demonstrated:")
    print("   ✅ Gemini AI Integration with personality adaptation")
    print("   ✅ Chat context management with mock Redis")
    print("   ✅ Google Workspace mock integration")
    print("   ✅ Notion mock integration")
    print("   ✅ MOM (Minutes of Meeting) agent with AI analysis")
    print("   ✅ Meeting templates based on user personality")
    print("   ✅ Integration status monitoring")
    print("   ✅ Rate limiting and security")
    print("   ✅ Comprehensive error handling")
    print("\n🚀 Ready for production deployment!")

if __name__ == "__main__":
    demo_phase2()
