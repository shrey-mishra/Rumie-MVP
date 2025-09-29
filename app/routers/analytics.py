from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.logging_config import get_logger
from app.services.gemini_service import gemini_service
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import requests
import json

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("analytics_router")

class AnalyticsRequest(BaseModel):
    platform: str
    date_range: str = "7d"  # 7d, 30d, 90d
    metrics: List[str] = ["views", "engagement", "growth"]

class CampaignSuggestion(BaseModel):
    content_type: str
    optimal_time: str
    target_audience: str
    suggested_topics: List[str]
    confidence_score: float

@router.get("/youtube/{user_id}")
@limiter.limit("10/minute")
async def get_youtube_analytics(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get YouTube analytics with Gemini insights"""
    logger.info("Fetching YouTube analytics", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("YouTube analytics failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Mock YouTube API call (in production, use real YouTube Data API)
        mock_youtube_data = {
            "channel_id": f"UC{user_id}",
            "subscriber_count": 1250,
            "total_views": 45000,
            "videos_count": 25,
            "recent_videos": [
                {
                    "video_id": "abc123",
                    "title": "Productivity Tips for Remote Work",
                    "views": 1200,
                    "likes": 85,
                    "comments": 23,
                    "published_at": "2025-09-28T10:00:00Z",
                    "duration": "8:45"
                },
                {
                    "video_id": "def456",
                    "title": "Time Management Strategies",
                    "views": 980,
                    "likes": 72,
                    "comments": 18,
                    "published_at": "2025-09-26T14:30:00Z",
                    "duration": "12:30"
                }
            ],
            "analytics": {
                "views_last_7_days": 3200,
                "watch_time_hours": 45.5,
                "average_view_duration": "3:45",
                "engagement_rate": 0.065,
                "click_through_rate": 0.042
            }
        }
        
        # Create prompt for Gemini analysis
        prompt = f"""
        Analyze this YouTube channel data and provide actionable insights:
        
        Channel Data:
        - Subscribers: {mock_youtube_data['subscriber_count']}
        - Total Views: {mock_youtube_data['total_views']}
        - Videos: {mock_youtube_data['videos_count']}
        - Recent Performance: {mock_youtube_data['analytics']['views_last_7_days']} views (7 days)
        - Engagement Rate: {mock_youtube_data['analytics']['engagement_rate']:.1%}
        - Average View Duration: {mock_youtube_data['analytics']['average_view_duration']}
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Provide:
        1. Performance analysis and trends
        2. Content optimization suggestions
        3. Engagement improvement strategies
        4. Personalized recommendations based on their personality
        5. Growth opportunities
        """
        
        # Get AI insights using Gemini
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        logger.info("YouTube analytics retrieved", user_id=user_id, confidence=ai_response["confidence"])
        
        return {
            "user_id": user_id,
            "platform": "youtube",
            "data": mock_youtube_data,
            "ai_insights": ai_response["response"],
            "confidence": ai_response["confidence"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error fetching YouTube analytics", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch YouTube analytics"
        )

@router.get("/twitch/{user_id}")
@limiter.limit("10/minute")
async def get_twitch_analytics(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get Twitch analytics with Gemini insights"""
    logger.info("Fetching Twitch analytics", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Twitch analytics failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Mock Twitch API call (in production, use real Twitch API)
        mock_twitch_data = {
            "channel_id": f"user_{user_id}",
            "followers": 850,
            "total_views": 25000,
            "streams_count": 15,
            "recent_streams": [
                {
                    "stream_id": "stream_001",
                    "title": "Coding Session: Building a Productivity App",
                    "viewers_peak": 45,
                    "duration_minutes": 120,
                    "started_at": "2025-09-28T19:00:00Z",
                    "category": "Software and Game Development",
                    "tags": ["coding", "productivity", "tutorial"]
                },
                {
                    "stream_id": "stream_002",
                    "title": "Morning Productivity Routine",
                    "viewers_peak": 32,
                    "duration_minutes": 90,
                    "started_at": "2025-09-26T08:00:00Z",
                    "category": "Just Chatting",
                    "tags": ["productivity", "morning", "routine"]
                }
            ],
            "analytics": {
                "avg_viewers": 28,
                "total_hours_streamed": 45,
                "followers_gained": 25,
                "chat_messages": 1200,
                "bits_earned": 150
            }
        }
        
        # Create prompt for Gemini analysis
        prompt = f"""
        Analyze this Twitch channel data and provide actionable insights:
        
        Channel Data:
        - Followers: {mock_twitch_data['followers']}
        - Total Views: {mock_twitch_data['total_views']}
        - Streams: {mock_twitch_data['streams_count']}
        - Average Viewers: {mock_twitch_data['analytics']['avg_viewers']}
        - Total Hours Streamed: {mock_twitch_data['analytics']['total_hours_streamed']}
        - Recent Followers Gained: {mock_twitch_data['analytics']['followers_gained']}
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Provide:
        1. Stream performance analysis
        2. Content strategy recommendations
        3. Engagement improvement tips
        4. Personalized streaming suggestions
        5. Growth and monetization opportunities
        """
        
        # Get AI insights using Gemini
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        logger.info("Twitch analytics retrieved", user_id=user_id, confidence=ai_response["confidence"])
        
        return {
            "user_id": user_id,
            "platform": "twitch",
            "data": mock_twitch_data,
            "ai_insights": ai_response["response"],
            "confidence": ai_response["confidence"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error fetching Twitch analytics", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch Twitch analytics"
        )

@router.post("/campaign-suggestions/{user_id}")
@limiter.limit("5/minute")
async def get_campaign_suggestions(
    user_id: int,
    analytics_request: AnalyticsRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get AI-powered campaign suggestions based on analytics"""
    logger.info("Generating campaign suggestions", user_id=user_id, platform=analytics_request.platform, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Campaign suggestions failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Create prompt for campaign suggestions
        prompt = f"""
        Generate personalized campaign suggestions for {analytics_request.platform} based on:
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Campaign Requirements:
        - Platform: {analytics_request.platform}
        - Date Range: {analytics_request.date_range}
        - Metrics Focus: {', '.join(analytics_request.metrics)}
        
        Provide:
        1. Content type recommendations
        2. Optimal posting/streaming times
        3. Target audience suggestions
        4. Topic ideas for next 7 days
        5. Engagement strategies
        6. Growth tactics
        """
        
        # Get AI suggestions using Gemini
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        # Parse AI response into structured suggestions
        suggestions = CampaignSuggestion(
            content_type="Educational Tutorial",
            optimal_time="19:00-21:00",
            target_audience="Remote workers and productivity enthusiasts",
            suggested_topics=[
                "Time Management Techniques",
                "Remote Work Productivity",
                "Digital Organization Tips",
                "Work-Life Balance",
                "Focus and Concentration"
            ],
            confidence_score=ai_response["confidence"]
        )
        
        logger.info("Campaign suggestions generated", user_id=user_id, confidence=ai_response["confidence"])
        
        return {
            "user_id": user_id,
            "platform": analytics_request.platform,
            "date_range": analytics_request.date_range,
            "suggestions": suggestions.dict(),
            "ai_insights": ai_response["response"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error generating campaign suggestions", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate campaign suggestions"
        )

@router.get("/cross-platform/{user_id}")
@limiter.limit("5/minute")
async def get_cross_platform_analytics(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get cross-platform analytics comparison"""
    logger.info("Getting cross-platform analytics", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Cross-platform analytics failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Mock cross-platform data
        cross_platform_data = {
            "user_id": user_id,
            "platforms": {
                "youtube": {
                    "subscribers": 1250,
                    "total_views": 45000,
                    "engagement_rate": 0.065,
                    "growth_rate": 0.12
                },
                "twitch": {
                    "followers": 850,
                    "total_views": 25000,
                    "avg_viewers": 28,
                    "growth_rate": 0.08
                },
                "twitter": {
                    "followers": 2100,
                    "tweets": 150,
                    "engagement_rate": 0.042,
                    "growth_rate": 0.15
                }
            },
            "insights": {
                "best_performing_platform": "youtube",
                "highest_engagement": "twitch",
                "fastest_growth": "twitter",
                "recommended_focus": "youtube"
            }
        }
        
        # Create prompt for cross-platform analysis
        prompt = f"""
        Analyze cross-platform performance and provide strategic insights:
        
        Platform Performance:
        - YouTube: {cross_platform_data['platforms']['youtube']['subscribers']} subscribers, {cross_platform_data['platforms']['youtube']['engagement_rate']:.1%} engagement
        - Twitch: {cross_platform_data['platforms']['twitch']['followers']} followers, {cross_platform_data['platforms']['twitch']['avg_viewers']} avg viewers
        - Twitter: {cross_platform_data['platforms']['twitter']['followers']} followers, {cross_platform_data['platforms']['twitter']['engagement_rate']:.1%} engagement
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Provide:
        1. Cross-platform performance analysis
        2. Platform-specific optimization strategies
        3. Content repurposing opportunities
        4. Resource allocation recommendations
        5. Growth strategy for next 30 days
        """
        
        # Get AI insights using Gemini
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        logger.info("Cross-platform analytics generated", user_id=user_id, confidence=ai_response["confidence"])
        
        return {
            "user_id": user_id,
            "data": cross_platform_data,
            "ai_insights": ai_response["response"],
            "confidence": ai_response["confidence"],
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error generating cross-platform analytics", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate cross-platform analytics"
        )
