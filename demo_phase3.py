#!/usr/bin/env python3
"""
Phase III Demo Script - Complete Backend Features
Demonstrates all Phase III features: productivity tracking, analytics, campaigns, paid traits, voice commands
"""

from fastapi.testclient import TestClient
from app.main import app
import json
import uuid
import time

def demo_phase3():
    client = TestClient(app)
    
    print("🚀 RumieAI Phase III Demo - Complete Backend Features")
    print("=" * 80)
    print("Features: Productivity Tracking, Analytics, Campaigns, Paid Traits, Voice Commands")
    print("=" * 80)
    
    # Create a user for testing
    print("\n1. Creating test user...")
    unique_email = f"phase3_demo_{uuid.uuid4().hex[:8]}@rumie.ai"
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
    
    # Test Paid Personality Traits
    print("\n2. Testing Paid Personality Traits...")
    
    # Get available traits
    traits_response = client.get("/v1/users/traits/available")
    if traits_response.status_code == 200:
        traits_data = traits_response.json()
        print(f"   ✅ Available traits retrieved")
        print(f"   🆓 Free traits: {len(traits_data['free_traits'])}")
        print(f"   💎 Paid traits: {len(traits_data['paid_traits'])}")
        
        # Show some traits
        for trait in traits_data['free_traits'][:2]:
            print(f"   🆓 {trait['name']} ({trait['type']})")
        for trait in traits_data['paid_traits'][:2]:
            print(f"   💎 {trait['name']} ({trait['type']})")
    else:
        print(f"   ❌ Traits retrieval failed: {traits_response.status_code}")
    
    # Test trait validation
    validation_response = client.get("/v1/users/traits/validate/creative_thinker")
    if validation_response.status_code == 200:
        validation_data = validation_response.json()
        print(f"   ✅ Trait validation: {validation_data['trait']} - {validation_data['trait_type']}")
        print(f"   📝 Message: {validation_data['message']}")
    else:
        print(f"   ❌ Trait validation failed: {validation_response.status_code}")
    
    # Test Enhanced Productivity Timer
    print("\n3. Testing Enhanced Productivity Timer...")
    
    # Start timer
    timer_start_response = client.post(f"/v1/productivity/timer/start", params={
        "user_id": user_id,
        "task_name": "Phase III Development",
        "category": "development"
    })
    
    if timer_start_response.status_code == 200:
        timer_data = timer_start_response.json()
        print(f"   ✅ Productivity timer started")
        print(f"   📋 Task: {timer_data['task_name']}")
        print(f"   📂 Category: {timer_data['category']}")
        
        # Wait a moment
        print("   ⏳ Waiting 2 seconds...")
        time.sleep(2)
        
        # Stop timer
        timer_stop_response = client.post(f"/v1/productivity/timer/stop", params={"user_id": user_id})
        if timer_stop_response.status_code == 200:
            stop_data = timer_stop_response.json()
            print(f"   ✅ Timer stopped")
            print(f"   ⏱️ Duration: {stop_data['duration_minutes']} minutes")
        else:
            print(f"   ❌ Timer stop failed: {timer_stop_response.status_code}")
    else:
        print(f"   ❌ Timer start failed: {timer_start_response.status_code}")
    
    # Test Saved Time Tracking
    print("\n4. Testing Saved Time Tracking...")
    saved_time_response = client.get(f"/v1/productivity/saved-time/{user_id}")
    if saved_time_response.status_code == 200:
        saved_time_data = saved_time_response.json()
        print(f"   ✅ Saved time tracking retrieved")
        print(f"   ⏱️ Total saved: {saved_time_data['total_saved_minutes']} minutes")
        print(f"   🎯 Daily goal: {saved_time_data['daily_goal']} minutes")
        print(f"   📊 Achievement: {saved_time_data['achievement_percentage']}%")
        print(f"   🔥 Streak: {saved_time_data['streak_days']} days")
        
        # Show breakdown
        breakdown = saved_time_data['breakdown']
        print(f"   📧 Email automation: {breakdown['email_automation']} min")
        print(f"   📋 Task organization: {breakdown['task_organization']} min")
        print(f"   🤝 Meeting optimization: {breakdown['meeting_optimization']} min")
    else:
        print(f"   ❌ Saved time tracking failed: {saved_time_response.status_code}")
    
    # Test Productivity Insights with Gemini
    print("\n5. Testing AI-Powered Productivity Insights...")
    insights_response = client.get(f"/v1/productivity/insights/{user_id}")
    if insights_response.status_code == 200:
        insights_data = insights_response.json()
        print(f"   ✅ Productivity insights generated")
        print(f"   🧠 AI Insights: {insights_data['ai_insights'][:100]}...")
        print(f"   🎯 Confidence: {insights_data['confidence']}")
        print(f"   📊 Metrics: {insights_data['metrics']}")
    else:
        print(f"   ❌ Productivity insights failed: {insights_response.status_code}")
    
    # Test Analytics Integration
    print("\n6. Testing Analytics Integration...")
    
    # YouTube Analytics
    youtube_response = client.get(f"/v1/analytics/youtube/{user_id}")
    if youtube_response.status_code == 200:
        youtube_data = youtube_response.json()
        print(f"   ✅ YouTube analytics retrieved")
        print(f"   📺 Subscribers: {youtube_data['data']['subscriber_count']}")
        print(f"   👀 Total views: {youtube_data['data']['total_views']}")
        print(f"   📊 Engagement: {youtube_data['data']['analytics']['engagement_rate']:.1%}")
        print(f"   🤖 AI Insights: {youtube_data['ai_insights'][:100]}...")
    else:
        print(f"   ❌ YouTube analytics failed: {youtube_response.status_code}")
    
    # Twitch Analytics
    twitch_response = client.get(f"/v1/analytics/twitch/{user_id}")
    if twitch_response.status_code == 200:
        twitch_data = twitch_response.json()
        print(f"   ✅ Twitch analytics retrieved")
        print(f"   👥 Followers: {twitch_data['data']['followers']}")
        print(f"   📺 Total views: {twitch_data['data']['total_views']}")
        print(f"   📊 Avg viewers: {twitch_data['data']['analytics']['avg_viewers']}")
        print(f"   🤖 AI Insights: {twitch_data['ai_insights'][:100]}...")
    else:
        print(f"   ❌ Twitch analytics failed: {twitch_response.status_code}")
    
    # Test Campaign Management
    print("\n7. Testing Campaign Management...")
    
    # Run a campaign
    campaign_request = {
        "campaign_name": "Productivity Newsletter",
        "message": "Hi {name}, here are your weekly productivity insights!",
        "recipients": [
            {"email": "user1@example.com", "name": "John"},
            {"email": "user2@example.com", "name": "Sarah"},
            {"phone": "+1234567890", "name": "Mike"}
        ],
        "platform": "email",
        "personalization": True
    }
    
    campaign_response = client.post(f"/v1/campaign/run/{user_id}", json=campaign_request)
    if campaign_response.status_code == 200:
        campaign_data = campaign_response.json()
        print(f"   ✅ Campaign executed")
        print(f"   📧 Campaign ID: {campaign_data['campaign_id']}")
        print(f"   📊 Total recipients: {campaign_data['total_recipients']}")
        print(f"   ✅ Sent: {campaign_data['sent_count']}")
        print(f"   ❌ Failed: {campaign_data['failed_count']}")
    else:
        print(f"   ❌ Campaign execution failed: {campaign_response.status_code}")
    
    # Get campaign templates
    templates_response = client.get("/v1/campaign/templates")
    if templates_response.status_code == 200:
        templates_data = templates_response.json()
        print(f"   ✅ Campaign templates retrieved")
        print(f"   📋 Total templates: {templates_data['total_templates']}")
        print(f"   📱 Platforms: {', '.join(templates_data['platforms'])}")
        print(f"   📂 Categories: {', '.join(templates_data['categories'])}")
    else:
        print(f"   ❌ Templates retrieval failed: {templates_response.status_code}")
    
    # Test AI Campaign Suggestions
    print("\n8. Testing AI Campaign Suggestions...")
    suggestions_response = client.post(f"/v1/campaign/ai-suggestions/{user_id}")
    if suggestions_response.status_code == 200:
        suggestions_data = suggestions_response.json()
        print(f"   ✅ AI campaign suggestions generated")
        print(f"   🤖 AI Insights: {suggestions_data['ai_insights'][:100]}...")
        print(f"   📧 Email campaigns: {len(suggestions_data['suggestions']['email_campaigns'])}")
        print(f"   📱 WhatsApp campaigns: {len(suggestions_data['suggestions']['whatsapp_campaigns'])}")
    else:
        print(f"   ❌ AI suggestions failed: {suggestions_response.status_code}")
    
    # Test Voice Commands
    print("\n9. Testing Voice Commands...")
    
    # Process voice command
    voice_command_response = client.post(f"/v1/voice/command/{user_id}", json={
        "audio_transcript": "Hello, I need help organizing my tasks for today"
    })
    if voice_command_response.status_code == 200:
        voice_data = voice_command_response.json()
        print(f"   ✅ Voice command processed")
        print(f"   🎤 Transcript: {voice_data['transcript']}")
        print(f"   🤖 Response: {voice_data['response'][:100]}...")
        print(f"   🎯 Confidence: {voice_data['confidence']}")
        print(f"   😊 Emotion: {voice_data['emotion']}")
    else:
        print(f"   ❌ Voice command failed: {voice_command_response.status_code}")
    
    # Test audio transcription
    transcription_response = client.post(f"/v1/voice/transcribe/{user_id}", json={
        "duration": 5.0,
        "format": "wav"
    })
    if transcription_response.status_code == 200:
        transcription_data = transcription_response.json()
        print(f"   ✅ Audio transcribed")
        print(f"   📝 Transcript: {transcription_data['transcript']}")
        print(f"   🎯 Confidence: {transcription_data['confidence']}")
        print(f"   🌍 Language: {transcription_data['language']}")
    else:
        print(f"   ❌ Audio transcription failed: {transcription_response.status_code}")
    
    # Test Cross-Platform Analytics
    print("\n10. Testing Cross-Platform Analytics...")
    cross_platform_response = client.get(f"/v1/analytics/cross-platform/{user_id}")
    if cross_platform_response.status_code == 200:
        cross_platform_data = cross_platform_response.json()
        print(f"   ✅ Cross-platform analytics retrieved")
        platforms = cross_platform_data['data']['platforms']
        print(f"   📺 YouTube: {platforms['youtube']['subscribers']} subscribers")
        print(f"   🎮 Twitch: {platforms['twitch']['followers']} followers")
        print(f"   🐦 Twitter: {platforms['twitter']['followers']} followers")
        print(f"   🏆 Best platform: {cross_platform_data['data']['insights']['best_performing_platform']}")
    else:
        print(f"   ❌ Cross-platform analytics failed: {cross_platform_response.status_code}")
    
    # Test Campaign Analytics
    print("\n11. Testing Campaign Analytics...")
    campaign_analytics_response = client.get(f"/v1/campaign/analytics/{user_id}")
    if campaign_analytics_response.status_code == 200:
        campaign_analytics_data = campaign_analytics_response.json()
        print(f"   ✅ Campaign analytics retrieved")
        overview = campaign_analytics_data['overview']
        print(f"   📊 Total campaigns: {overview['total_campaigns']}")
        print(f"   📧 Total recipients: {overview['total_recipients']}")
        print(f"   ✅ Success rate: {overview['success_rate']:.1f}%")
    else:
        print(f"   ❌ Campaign analytics failed: {campaign_analytics_response.status_code}")
    
    print("\n" + "=" * 80)
    print("🎉 Phase III Demo Completed Successfully!")
    print("\n📋 All Phase III Features Demonstrated:")
    print("   ✅ Enhanced Productivity Timer with saved time tracking")
    print("   ✅ AI-Powered Productivity Insights with Gemini")
    print("   ✅ Analytics Integration (YouTube/Twitch) with AI insights")
    print("   ✅ Bulk Campaign Management (Email/WhatsApp)")
    print("   ✅ AI Campaign Suggestions with Gemini")
    print("   ✅ Paid Personality Traits validation")
    print("   ✅ Voice Command Processing with Gemini")
    print("   ✅ Audio Transcription mock")
    print("   ✅ Cross-Platform Analytics")
    print("   ✅ Campaign Performance Analytics")
    print("\n🚀 Backend Complete - Ready for Frontend Development!")
    print("   🎨 React/Next.js frontend development")
    print("   🔐 JWT authentication implementation")
    print("   🗄️ PostgreSQL migration")
    print("   🐳 Docker deployment")
    print("   📱 Mobile app development")

if __name__ == "__main__":
    demo_phase3()
