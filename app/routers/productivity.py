from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("productivity_router")

# Mock storage for productivity data
productivity_data = {}

class TimerSession(BaseModel):
    user_id: int
    task_name: str
    category: str
    start_time: str
    end_time: Optional[str] = None
    duration_minutes: Optional[int] = None
    is_active: bool = True

class ProductivityAnalytics(BaseModel):
    user_id: int
    total_focus_time: int  # minutes
    sessions_completed: int
    average_session_duration: float
    most_productive_category: str
    daily_breakdown: List[Dict[str, Any]]
    weekly_trend: List[Dict[str, Any]]

@router.post("/timer/start")
@limiter.limit("10/minute")
def start_productivity_timer(
    user_id: int,
    task_name: str,
    category: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Start a productivity timer session"""
    logger.info(
        "Starting productivity timer", 
        user_id=user_id, 
        task_name=task_name, 
        category=category,
        client_ip=get_remote_address(request)
    )
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Timer start failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has active timer
    user_key = f"timer:{user_id}"
    if user_key in productivity_data and productivity_data[user_key].get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active timer session"
        )
    
    # Create new timer session
    timer_session = {
        "user_id": user_id,
        "task_name": task_name,
        "category": category,
        "start_time": datetime.utcnow().isoformat(),
        "end_time": None,
        "duration_minutes": None,
        "is_active": True
    }
    
    productivity_data[user_key] = timer_session
    
    logger.info("Productivity timer started", user_id=user_id, task_name=task_name)
    
    return {
        "status": "timer_started",
        "session_id": user_key,
        "start_time": timer_session["start_time"],
        "task_name": task_name,
        "category": category
    }

@router.post("/timer/stop")
@limiter.limit("10/minute")
def stop_productivity_timer(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Stop the active productivity timer session"""
    logger.info("Stopping productivity timer", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Timer stop failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_key = f"timer:{user_id}"
    if user_key not in productivity_data or not productivity_data[user_key].get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active timer session found"
        )
    
    # Calculate duration
    start_time = datetime.fromisoformat(productivity_data[user_key]["start_time"])
    end_time = datetime.utcnow()
    duration_minutes = int((end_time - start_time).total_seconds() / 60)
    
    # Update timer session
    productivity_data[user_key].update({
        "end_time": end_time.isoformat(),
        "duration_minutes": duration_minutes,
        "is_active": False
    })
    
    # Store completed session
    session_key = f"session:{user_id}:{end_time.strftime('%Y%m%d%H%M%S')}"
    productivity_data[session_key] = productivity_data[user_key].copy()
    
    logger.info("Productivity timer stopped", user_id=user_id, duration_minutes=duration_minutes)
    
    return {
        "status": "timer_stopped",
        "session_id": user_key,
        "duration_minutes": duration_minutes,
        "task_name": productivity_data[user_key]["task_name"],
        "category": productivity_data[user_key]["category"]
    }

@router.get("/timer/status/{user_id}")
@limiter.limit("20/minute")
def get_timer_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get current timer status for a user"""
    logger.info("Getting timer status", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Timer status failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user_key = f"timer:{user_id}"
    if user_key not in productivity_data:
        return {
            "user_id": user_id,
            "has_active_timer": False,
            "current_session": None
        }
    
    session = productivity_data[user_key]
    if not session.get("is_active", False):
        return {
            "user_id": user_id,
            "has_active_timer": False,
            "current_session": None
        }
    
    # Calculate current duration
    start_time = datetime.fromisoformat(session["start_time"])
    current_duration = int((datetime.utcnow() - start_time).total_seconds() / 60)
    
    return {
        "user_id": user_id,
        "has_active_timer": True,
        "current_session": {
            "task_name": session["task_name"],
            "category": session["category"],
            "start_time": session["start_time"],
            "current_duration_minutes": current_duration
        }
    }

@router.get("/analytics/{user_id}")
@limiter.limit("10/minute")
def get_productivity_analytics(
    user_id: int,
    request: Request,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """Get productivity analytics for a user"""
    logger.info("Getting productivity analytics", user_id=user_id, days=days, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Analytics failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's completed sessions
    user_sessions = []
    for key, session in productivity_data.items():
        if key.startswith(f"session:{user_id}:") and not session.get("is_active", False):
            user_sessions.append(session)
    
    # Calculate analytics
    total_focus_time = sum(session.get("duration_minutes", 0) for session in user_sessions)
    sessions_completed = len(user_sessions)
    average_session_duration = total_focus_time / sessions_completed if sessions_completed > 0 else 0
    
    # Find most productive category
    category_times = {}
    for session in user_sessions:
        category = session.get("category", "uncategorized")
        duration = session.get("duration_minutes", 0)
        category_times[category] = category_times.get(category, 0) + duration
    
    most_productive_category = max(category_times.items(), key=lambda x: x[1])[0] if category_times else "none"
    
    # Generate daily breakdown (mock data for demo)
    daily_breakdown = []
    for i in range(days):
        date = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        daily_breakdown.append({
            "date": date,
            "focus_time_minutes": min(480, total_focus_time // days + (i * 10)),  # Mock data
            "sessions_completed": max(1, sessions_completed // days),
            "most_productive_category": most_productive_category
        })
    
    # Generate weekly trend (mock data for demo)
    weekly_trend = []
    for i in range(4):  # Last 4 weeks
        week_start = (datetime.utcnow() - timedelta(weeks=i)).strftime("%Y-%m-%d")
        weekly_trend.append({
            "week": week_start,
            "total_focus_time": min(2000, total_focus_time + (i * 100)),
            "sessions_completed": max(5, sessions_completed + (i * 2)),
            "average_session_duration": average_session_duration + (i * 5)
        })
    
    logger.info("Productivity analytics generated", user_id=user_id, total_sessions=sessions_completed)
    
    return ProductivityAnalytics(
        user_id=user_id,
        total_focus_time=total_focus_time,
        sessions_completed=sessions_completed,
        average_session_duration=average_session_duration,
        most_productive_category=most_productive_category,
        daily_breakdown=daily_breakdown,
        weekly_trend=weekly_trend
    )

@router.get("/sessions/{user_id}")
@limiter.limit("20/minute")
def get_user_sessions(
    user_id: int,
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's productivity sessions"""
    logger.info("Getting user sessions", user_id=user_id, limit=limit, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Sessions request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's sessions
    user_sessions = []
    for key, session in productivity_data.items():
        if key.startswith(f"session:{user_id}:") and not session.get("is_active", False):
            user_sessions.append(session)
    
    # Sort by start time (newest first)
    user_sessions.sort(key=lambda x: x.get("start_time", ""), reverse=True)
    
    # Limit results
    user_sessions = user_sessions[:limit]
    
    logger.info("User sessions retrieved", user_id=user_id, session_count=len(user_sessions))
    
    return {
        "user_id": user_id,
        "sessions": user_sessions,
        "total_sessions": len(user_sessions),
        "limit": limit
    }

@router.get("/saved-time/{user_id}")
@limiter.limit("10/minute")
def get_saved_time_tracking(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get saved time tracking from integrations"""
    logger.info("Getting saved time tracking", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Saved time request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock saved time calculation from integrations
    # In production, this would calculate from actual integration data
    saved_time_data = {
        "user_id": user_id,
        "total_saved_minutes": 45,  # Mock: 45 minutes saved today
        "breakdown": {
            "email_automation": 15,  # 5 emails × 3 min saved each
            "task_organization": 20,  # 4 tasks × 5 min saved each
            "meeting_optimization": 10  # 2 meetings × 5 min saved each
        },
        "daily_goal": 60,  # 1 hour goal
        "achievement_percentage": 75,  # 45/60 = 75%
        "streak_days": 7,  # 7 days in a row
        "last_updated": datetime.utcnow().isoformat()
    }
    
    logger.info("Saved time tracking retrieved", user_id=user_id, total_saved=saved_time_data["total_saved_minutes"])
    
    return saved_time_data

@router.get("/insights/{user_id}")
@limiter.limit("5/minute")
async def get_productivity_insights(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get AI-powered productivity insights using Gemini"""
    logger.info("Getting productivity insights", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Insights request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's productivity data
    user_sessions = []
    for key, session in productivity_data.items():
        if key.startswith(f"session:{user_id}:") and not session.get("is_active", False):
            user_sessions.append(session)
    
    # Calculate productivity metrics
    total_focus_time = sum(session.get("duration_minutes", 0) for session in user_sessions)
    sessions_count = len(user_sessions)
    average_session = total_focus_time / sessions_count if sessions_count > 0 else 0
    
    # Create prompt for Gemini analysis
    prompt = f"""
    Analyze this user's productivity data and provide personalized insights:
    
    User Profile:
    - Personality: {user.personality_trait}
    - Mode Preference: {user.mode_pref}
    
    Productivity Data:
    - Total focus time: {total_focus_time} minutes
    - Sessions completed: {sessions_count}
    - Average session duration: {average_session:.1f} minutes
    
    Provide:
    1. Personalized productivity insights based on their personality
    2. Specific recommendations for improvement
    3. Motivational message tailored to their mode preference
    4. Suggested focus areas for tomorrow
    """
    
    try:
        # Get AI insights using Gemini service
        from app.services.gemini_service import gemini_service
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        insights = {
            "user_id": user_id,
            "personality_trait": user.personality_trait,
            "mode_pref": user.mode_pref,
            "ai_insights": ai_response["response"],
            "confidence": ai_response["confidence"],
            "metrics": {
                "total_focus_time": total_focus_time,
                "sessions_completed": sessions_count,
                "average_session_duration": average_session
            },
            "generated_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Productivity insights generated", user_id=user_id, confidence=ai_response["confidence"])
        
        return insights
        
    except Exception as e:
        logger.error("Error generating productivity insights", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate productivity insights"
        )
