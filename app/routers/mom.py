from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.logging_config import get_logger
from app.services.gemini_service import gemini_service
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("mom_router")

class MeetingTranscript(BaseModel):
    transcript: str
    meeting_title: str
    participants: List[str]
    duration_minutes: int

class MeetingAnalysis(BaseModel):
    summary: str
    key_points: List[str]
    action_items: List[Dict[str, Any]]
    next_steps: List[str]
    participants: List[str]
    duration: int
    confidence_score: float

@router.post("/analyze/{user_id}", response_model=MeetingAnalysis)
@limiter.limit("5/minute")
async def analyze_meeting(
    user_id: int,
    meeting_data: MeetingTranscript,
    request: Request,
    db: Session = Depends(get_db)
):
    """Analyze meeting transcript using Gemini AI for MOM generation"""
    logger.info(
        "Analyzing meeting transcript", 
        user_id=user_id, 
        meeting_title=meeting_data.meeting_title,
        participants_count=len(meeting_data.participants),
        duration=meeting_data.duration_minutes,
        client_ip=get_remote_address(request)
    )
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Meeting analysis failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Create tailored prompt for meeting analysis
        analysis_prompt = f"""
        Analyze this meeting transcript and provide a comprehensive MOM (Minutes of Meeting) analysis.
        
        Meeting Title: {meeting_data.meeting_title}
        Participants: {', '.join(meeting_data.participants)}
        Duration: {meeting_data.duration_minutes} minutes
        
        Transcript:
        {meeting_data.transcript}
        
        Please provide:
        1. Executive summary (2-3 sentences)
        2. Key discussion points (bullet points)
        3. Action items with owners and deadlines
        4. Next steps and follow-ups
        5. Important decisions made
        
        Format the response as a structured analysis suitable for business documentation.
        """
        
        # Get AI response using Gemini service
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=analysis_prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        # Parse AI response into structured format
        analysis_result = parse_meeting_analysis(
            ai_response["response"],
            meeting_data.participants,
            meeting_data.duration_minutes
        )
        
        logger.info(
            "Meeting analysis completed", 
            user_id=user_id, 
            confidence=ai_response.get("confidence", 0.0),
            action_items_count=len(analysis_result["action_items"])
        )
        
        return MeetingAnalysis(**analysis_result)
        
    except Exception as e:
        logger.error("Error analyzing meeting", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze meeting transcript"
        )

@router.get("/templates/{user_id}")
@limiter.limit("10/minute")
def get_meeting_templates(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get MOM templates based on user preferences"""
    logger.info("Fetching meeting templates", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Template request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Generate templates based on user personality and mode
    templates = generate_templates_for_user(user.personality_trait, user.mode_pref)
    
    logger.info("Templates retrieved", user_id=user_id, template_count=len(templates))
    
    return {
        "user_id": user_id,
        "personality_trait": user.personality_trait,
        "mode_pref": user.mode_pref,
        "templates": templates
    }

@router.get("/history/{user_id}")
@limiter.limit("20/minute")
def get_meeting_history(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user's meeting analysis history"""
    logger.info("Fetching meeting history", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("History request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Mock meeting history
    meeting_history = [
        {
            "id": "meeting_001",
            "title": "Weekly Team Standup",
            "date": "2025-09-28T10:00:00Z",
            "duration": 30,
            "participants": ["user@company.com", "manager@company.com", "colleague@company.com"],
            "action_items": 3,
            "status": "completed"
        },
        {
            "id": "meeting_002", 
            "title": "Project Planning Session",
            "date": "2025-09-27T14:00:00Z",
            "duration": 60,
            "participants": ["user@company.com", "project-lead@company.com"],
            "action_items": 5,
            "status": "in_progress"
        }
    ]
    
    logger.info("Meeting history retrieved", user_id=user_id, meetings_count=len(meeting_history))
    
    return {
        "user_id": user_id,
        "meetings": meeting_history,
        "total_meetings": len(meeting_history),
        "last_updated": "2025-09-29T10:30:00Z"
    }

def parse_meeting_analysis(ai_response: str, participants: List[str], duration: int) -> Dict[str, Any]:
    """Parse AI response into structured meeting analysis"""
    # This would contain more sophisticated parsing logic
    # For now, return a structured mock response
    return {
        "summary": ai_response[:200] + "..." if len(ai_response) > 200 else ai_response,
        "key_points": [
            "Project timeline discussed",
            "Resource allocation finalized", 
            "Risk mitigation strategies identified"
        ],
        "action_items": [
            {
                "task": "Prepare project proposal",
                "owner": participants[0] if participants else "TBD",
                "deadline": "2025-10-05T17:00:00Z",
                "priority": "high"
            },
            {
                "task": "Schedule follow-up meeting",
                "owner": participants[1] if len(participants) > 1 else "TBD",
                "deadline": "2025-10-01T12:00:00Z",
                "priority": "medium"
            }
        ],
        "next_steps": [
            "Review project requirements",
            "Prepare technical specifications",
            "Schedule stakeholder review"
        ],
        "participants": participants,
        "duration": duration,
        "confidence_score": 0.85
    }

def generate_templates_for_user(personality_trait: str, mode_pref: str) -> List[Dict[str, Any]]:
    """Generate MOM templates based on user personality and mode"""
    base_templates = [
        {
            "id": "template_001",
            "name": "Standard Meeting",
            "sections": ["Agenda", "Discussion", "Decisions", "Action Items"],
            "description": "Basic meeting template for general use"
        },
        {
            "id": "template_002", 
            "name": "Project Review",
            "sections": ["Project Status", "Milestones", "Risks", "Next Steps"],
            "description": "Template for project review meetings"
        }
    ]
    
    # Customize based on personality
    if personality_trait == "efficient_organizer":
        base_templates.append({
            "id": "template_003",
            "name": "Efficient Standup",
            "sections": ["Yesterday's Progress", "Today's Plan", "Blockers", "Quick Updates"],
            "description": "Streamlined template for efficient team updates"
        })
    elif personality_trait == "creative_thinker":
        base_templates.append({
            "id": "template_004",
            "name": "Brainstorming Session",
            "sections": ["Ideas", "Innovation Points", "Creative Solutions", "Implementation"],
            "description": "Template for creative brainstorming sessions"
        })
    
    return base_templates
