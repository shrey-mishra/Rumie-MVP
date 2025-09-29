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
import json
import uuid

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("campaign_router")

# Mock storage for campaigns
campaign_data = {}

class CampaignRequest(BaseModel):
    campaign_name: str
    message: str
    recipients: List[Dict[str, Any]]  # [{"email": "user@example.com", "name": "User"}, {"phone": "+1234567890", "name": "User"}]
    platform: str  # "email" or "whatsapp"
    scheduled_time: Optional[str] = None
    personalization: bool = True

class CampaignResponse(BaseModel):
    campaign_id: str
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    scheduled_time: Optional[str]
    created_at: str

class CampaignTemplate(BaseModel):
    template_id: str
    name: str
    content: str
    platform: str
    category: str
    personalization_fields: List[str]

@router.post("/run/{user_id}", response_model=CampaignResponse)
@limiter.limit("5/minute")
async def run_campaign(
    user_id: int,
    campaign_request: CampaignRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Run a bulk campaign (email/WhatsApp mock)"""
    logger.info(
        "Running campaign", 
        user_id=user_id, 
        campaign_name=campaign_request.campaign_name,
        platform=campaign_request.platform,
        recipients_count=len(campaign_request.recipients),
        client_ip=get_remote_address(request)
    )
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Campaign run failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Generate campaign ID
        campaign_id = str(uuid.uuid4())
        
        # Mock campaign execution
        total_recipients = len(campaign_request.recipients)
        sent_count = int(total_recipients * 0.95)  # 95% success rate
        failed_count = total_recipients - sent_count
        
        # Store campaign data
        campaign_info = {
            "campaign_id": campaign_id,
            "user_id": user_id,
            "campaign_name": campaign_request.campaign_name,
            "message": campaign_request.message,
            "platform": campaign_request.platform,
            "recipients": campaign_request.recipients,
            "total_recipients": total_recipients,
            "sent_count": sent_count,
            "failed_count": failed_count,
            "status": "completed",
            "scheduled_time": campaign_request.scheduled_time,
            "created_at": datetime.utcnow().isoformat(),
            "personalization": campaign_request.personalization
        }
        
        campaign_data[campaign_id] = campaign_info
        
        logger.info(
            "Campaign completed", 
            user_id=user_id, 
            campaign_id=campaign_id,
            sent_count=sent_count,
            failed_count=failed_count
        )
        
        return CampaignResponse(
            campaign_id=campaign_id,
            status="completed",
            total_recipients=total_recipients,
            sent_count=sent_count,
            failed_count=failed_count,
            scheduled_time=campaign_request.scheduled_time,
            created_at=campaign_info["created_at"]
        )
        
    except Exception as e:
        logger.error("Error running campaign", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run campaign"
        )

@router.get("/campaigns/{user_id}")
@limiter.limit("20/minute")
def get_user_campaigns(
    user_id: int,
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's campaign history"""
    logger.info("Getting user campaigns", user_id=user_id, limit=limit, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Campaigns request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's campaigns
    user_campaigns = [
        campaign for campaign in campaign_data.values()
        if campaign.get("user_id") == user_id
    ]
    
    # Sort by creation time (newest first)
    user_campaigns.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit results
    user_campaigns = user_campaigns[:limit]
    
    logger.info("User campaigns retrieved", user_id=user_id, campaign_count=len(user_campaigns))
    
    return {
        "user_id": user_id,
        "campaigns": user_campaigns,
        "total_campaigns": len(user_campaigns),
        "limit": limit
    }

@router.get("/templates")
@limiter.limit("30/minute")
def get_campaign_templates(request: Request):
    """Get available campaign templates"""
    logger.info("Getting campaign templates", client_ip=get_remote_address(request))
    
    templates = [
        {
            "template_id": "email_001",
            "name": "Productivity Newsletter",
            "content": "Hi {name}, here are this week's productivity tips: {content}",
            "platform": "email",
            "category": "newsletter",
            "personalization_fields": ["name", "content"]
        },
        {
            "template_id": "whatsapp_001",
            "name": "Quick Update",
            "content": "Hey {name}! Quick update: {message}",
            "platform": "whatsapp",
            "category": "update",
            "personalization_fields": ["name", "message"]
        },
        {
            "template_id": "email_002",
            "name": "Meeting Reminder",
            "content": "Hi {name}, reminder about our meeting at {time}",
            "platform": "email",
            "category": "reminder",
            "personalization_fields": ["name", "time"]
        },
        {
            "template_id": "whatsapp_002",
            "name": "Event Invitation",
            "content": "Hi {name}! You're invited to {event} on {date}",
            "platform": "whatsapp",
            "category": "invitation",
            "personalization_fields": ["name", "event", "date"]
        }
    ]
    
    return {
        "templates": templates,
        "total_templates": len(templates),
        "platforms": ["email", "whatsapp"],
        "categories": ["newsletter", "update", "reminder", "invitation"]
    }

@router.post("/ai-suggestions/{user_id}")
@limiter.limit("5/minute")
async def get_ai_campaign_suggestions(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get AI-powered campaign suggestions using Gemini"""
    logger.info("Generating AI campaign suggestions", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("AI suggestions failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get user's campaign history for context
        user_campaigns = [
            campaign for campaign in campaign_data.values()
            if campaign.get("user_id") == user_id
        ]
        
        # Create prompt for AI suggestions
        prompt = f"""
        Generate personalized campaign suggestions based on:
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Campaign History:
        - Total Campaigns: {len(user_campaigns)}
        - Recent Platforms: {', '.join(set(c.get('platform', '') for c in user_campaigns[-3:]))}
        
        Provide:
        1. Content suggestions for email campaigns
        2. WhatsApp message templates
        3. Optimal sending times
        4. Personalization strategies
        5. Engagement improvement tips
        6. A/B testing recommendations
        """
        
        # Get AI suggestions using Gemini
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        # Generate structured suggestions
        suggestions = {
            "user_id": user_id,
            "ai_insights": ai_response["response"],
            "confidence": ai_response["confidence"],
            "suggestions": {
                "email_campaigns": [
                    "Weekly productivity newsletter",
                    "Personalized task reminders",
                    "Achievement celebrations"
                ],
                "whatsapp_campaigns": [
                    "Quick daily check-ins",
                    "Motivational messages",
                    "Event notifications"
                ],
                "optimal_times": {
                    "email": "09:00-10:00, 14:00-15:00",
                    "whatsapp": "18:00-20:00"
                },
                "personalization_tips": [
                    "Use recipient's name in subject line",
                    "Reference their recent activity",
                    "Tailor tone to their personality"
                ]
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("AI campaign suggestions generated", user_id=user_id, confidence=ai_response["confidence"])
        
        return suggestions
        
    except Exception as e:
        logger.error("Error generating AI suggestions", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI suggestions"
        )

@router.get("/analytics/{user_id}")
@limiter.limit("10/minute")
def get_campaign_analytics(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get campaign performance analytics"""
    logger.info("Getting campaign analytics", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Campaign analytics failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's campaigns
    user_campaigns = [
        campaign for campaign in campaign_data.values()
        if campaign.get("user_id") == user_id
    ]
    
    # Calculate analytics
    total_campaigns = len(user_campaigns)
    total_recipients = sum(campaign.get("total_recipients", 0) for campaign in user_campaigns)
    total_sent = sum(campaign.get("sent_count", 0) for campaign in user_campaigns)
    total_failed = sum(campaign.get("failed_count", 0) for campaign in user_campaigns)
    
    # Platform breakdown
    platform_stats = {}
    for campaign in user_campaigns:
        platform = campaign.get("platform", "unknown")
        if platform not in platform_stats:
            platform_stats[platform] = {"campaigns": 0, "recipients": 0, "sent": 0}
        platform_stats[platform]["campaigns"] += 1
        platform_stats[platform]["recipients"] += campaign.get("total_recipients", 0)
        platform_stats[platform]["sent"] += campaign.get("sent_count", 0)
    
    analytics = {
        "user_id": user_id,
        "overview": {
            "total_campaigns": total_campaigns,
            "total_recipients": total_recipients,
            "total_sent": total_sent,
            "total_failed": total_failed,
            "success_rate": (total_sent / total_recipients * 100) if total_recipients > 0 else 0
        },
        "platform_breakdown": platform_stats,
        "recent_campaigns": user_campaigns[:5],  # Last 5 campaigns
        "generated_at": datetime.utcnow().isoformat()
    }
    
    logger.info("Campaign analytics retrieved", user_id=user_id, total_campaigns=total_campaigns)
    
    return analytics

@router.delete("/campaign/{campaign_id}")
@limiter.limit("10/minute")
def delete_campaign(
    campaign_id: str,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a campaign"""
    logger.info("Deleting campaign", campaign_id=campaign_id, user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Campaign deletion failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if campaign exists and belongs to user
    if campaign_id not in campaign_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found"
        )
    
    campaign = campaign_data[campaign_id]
    if campaign.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this campaign"
        )
    
    # Delete campaign
    del campaign_data[campaign_id]
    
    logger.info("Campaign deleted", campaign_id=campaign_id, user_id=user_id)
    
    return {
        "status": "deleted",
        "campaign_id": campaign_id,
        "user_id": user_id
    }
