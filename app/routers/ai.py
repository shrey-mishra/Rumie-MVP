from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.services.gemini_service import gemini_service
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("ai_router")

class AIRequest(BaseModel):
    user_id: int
    message: str

class AIResponse(BaseModel):
    response: str
    confidence: float
    emotion: str
    personality_match: str
    mode_adapted: str

@router.post("/chat", response_model=AIResponse)
@limiter.limit("20/minute")
async def chat_with_ai(
    ai_request: AIRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Chat with AI using user's personality and preferences"""
    logger.info(
        "AI chat request", 
        user_id=ai_request.user_id, 
        message_length=len(ai_request.message),
        client_ip=get_remote_address(request)
    )
    
    # Get user information
    user = get_user_by_id(db, user_id=ai_request.user_id)
    if not user:
        logger.warning("AI chat failed - user not found", user_id=ai_request.user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Generate empathetic response
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=ai_request.message,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        logger.info(
            "AI response generated", 
            user_id=ai_request.user_id, 
            confidence=ai_response.get("confidence", 0.0)
        )
        
        return AIResponse(
            response=ai_response["response"],
            confidence=ai_response["confidence"],
            emotion=ai_response["emotion"],
            personality_match=ai_response.get("personality_match", user.personality_trait),
            mode_adapted=ai_response.get("mode_adapted", user.mode_pref)
        )
        
    except Exception as e:
        logger.error("Error generating AI response", error=str(e), user_id=ai_request.user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate AI response"
        )
