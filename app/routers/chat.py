from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_redis
from app.crud import get_user_by_id
from app.logging_config import get_logger
from app.services.gemini_service import gemini_service
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import uuid
from datetime import datetime

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("chat_router")

# Mock Redis for session management (will be replaced with real Redis in production)
mock_redis = {}
SESSION_TTL = 3600  # 1 hour in seconds

class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: str
    message_id: str

class ChatRequest(BaseModel):
    message: str
    context: Optional[List[Dict[str, Any]]] = None

class ChatResponse(BaseModel):
    response: str
    message_id: str
    timestamp: str
    confidence: float
    emotion: str
    personality_match: str
    mode_adapted: str

class ChatContext(BaseModel):
    user_id: int
    chat_history: List[ChatMessage]
    last_updated: str
    session_id: str

@router.post("/response/{user_id}", response_model=ChatResponse)
@limiter.limit("20/minute")
async def get_chat_response(
    user_id: int,
    chat_request: ChatRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get AI chat response using Gemini with user context and personality"""
    logger.info(
        "Processing chat request", 
        user_id=user_id, 
        message_length=len(chat_request.message),
        has_context=bool(chat_request.context),
        client_ip=get_remote_address(request)
    )
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Chat request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Get chat context from Redis with TTL
        context_key = f"chat:{user_id}"
        try:
            context_data = redis_client.get(context_key)
            chat_history = json.loads(context_data) if context_data else []
        except Exception as e:
            logger.warning("Redis error, falling back to mock", error=str(e))
            # Fallback to mock Redis
            context_data = get_session_data(context_key)
            chat_history = json.loads(context_data) if context_data else []
            
            # Cleanup expired sessions periodically
            if len(mock_redis) > 100:  # Only cleanup when we have many sessions
                cleanup_expired_sessions()
        
        # Add user message to history
        user_message = {
            "role": "user",
            "content": chat_request.message,
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        chat_history.append(user_message)
        
        # Create tailored prompt with context and personality
        context_str = format_chat_context(chat_history[-5:])  # Last 5 messages for context
        
        # Enhanced prompt with better context integration
        tailored_prompt = f"""
        You are an empathetic AI assistant responding to a user with {user.personality_trait} personality in {user.mode_pref} mode.
        
        User Profile:
        - Personality: {user.personality_trait}
        - Preferred Mode: {user.mode_pref}
        - Communication Style: Adapt to their personality and mode preferences
        
        Previous conversation context:
        {context_str}
        
        Current user message: {chat_request.message}
        
        Instructions:
        1. Respond in a way that matches their {user.personality_trait} personality
        2. Use their preferred {user.mode_pref} communication mode
        3. Reference previous conversation context when relevant
        4. Be empathetic, helpful, and maintain conversation continuity
        5. Keep responses concise but comprehensive
        """
        
        # Get AI response using Gemini service
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=tailored_prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        # Create assistant message
        assistant_message = {
            "role": "assistant",
            "content": ai_response["response"],
            "timestamp": datetime.utcnow().isoformat(),
            "message_id": str(uuid.uuid4())
        }
        chat_history.append(assistant_message)
        
        # Update context in mock Redis with TTL
        set_session_data(context_key, json.dumps(chat_history[-20:]))  # Keep last 20 messages
        
        logger.info(
            "Chat response generated", 
            user_id=user_id, 
            confidence=ai_response.get("confidence", 0.0),
            response_length=len(ai_response["response"])
        )
        
        return ChatResponse(
            response=ai_response["response"],
            message_id=assistant_message["message_id"],
            timestamp=assistant_message["timestamp"],
            confidence=ai_response["confidence"],
            emotion=ai_response["emotion"],
            personality_match=ai_response.get("personality_match", user.personality_trait),
            mode_adapted=ai_response.get("mode_adapted", user.mode_pref)
        )
        
    except Exception as e:
        logger.error("Error generating chat response", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate chat response"
        )

@router.get("/context/{user_id}", response_model=ChatContext)
@limiter.limit("30/minute")
async def get_chat_context(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    redis_client = Depends(get_redis)
):
    """Get chat context and history for a user"""
    logger.info("Fetching chat context", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Context request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get chat history from mock Redis with TTL check
    context_key = f"chat:{user_id}"
    context_data = get_session_data(context_key)
    chat_history = json.loads(context_data) if context_data else []
    
    # Convert to ChatMessage objects
    chat_messages = [
        ChatMessage(**msg) for msg in chat_history
    ]
    
    logger.info("Chat context retrieved", user_id=user_id, message_count=len(chat_messages))
    
    return ChatContext(
        user_id=user_id,
        chat_history=chat_messages,
        last_updated=datetime.utcnow().isoformat(),
        session_id=context_key
    )

@router.post("/context/{user_id}")
@limiter.limit("10/minute")
async def set_chat_context(
    user_id: int,
    context: ChatContext,
    request: Request,
    db: Session = Depends(get_db)
):
    """Set chat context for a user"""
    logger.info("Setting chat context", user_id=user_id, message_count=len(context.chat_history), client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Context update failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Convert ChatMessage objects to dicts
    chat_history = [msg.dict() for msg in context.chat_history]
    
    # Update context in mock Redis with TTL
    context_key = f"chat:{user_id}"
    set_session_data(context_key, json.dumps(chat_history))
    
    logger.info("Chat context updated", user_id=user_id, message_count=len(chat_history))
    
    return {"status": "updated", "message_count": len(chat_history)}

@router.delete("/context/{user_id}")
@limiter.limit("5/minute")
async def clear_chat_context(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Clear chat context for a user"""
    logger.info("Clearing chat context", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Context clear failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Clear context from mock Redis
    context_key = f"chat:{user_id}"
    if context_key in mock_redis:
        del mock_redis[context_key]
    
    logger.info("Chat context cleared", user_id=user_id)
    
    return {"status": "cleared", "user_id": user_id}

@router.get("/sessions/{user_id}")
@limiter.limit("20/minute")
async def get_chat_sessions(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all chat sessions for a user"""
    logger.info("Fetching chat sessions", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Sessions request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get all sessions for user (in a real implementation, this would query a database)
    sessions = []
    for key, value in mock_redis.items():
        if key.startswith(f"chat:{user_id}"):
            chat_data = json.loads(value) if value else []
            if chat_data:
                sessions.append({
                    "session_id": key,
                    "message_count": len(chat_data),
                    "last_message": chat_data[-1] if chat_data else None,
                    "created_at": chat_data[0]["timestamp"] if chat_data else None
                })
    
    logger.info("Chat sessions retrieved", user_id=user_id, session_count=len(sessions))
    
    return {
        "user_id": user_id,
        "sessions": sessions,
        "total_sessions": len(sessions)
    }

def get_session_data(key: str) -> Optional[str]:
    """Get session data with TTL check"""
    if key not in mock_redis:
        return None
    
    session_data = mock_redis[key]
    if isinstance(session_data, dict) and "expires_at" in session_data:
        if datetime.utcnow().timestamp() > session_data["expires_at"]:
            # Session expired, remove it
            del mock_redis[key]
            return None
        return session_data["data"]
    
    # Legacy format without TTL
    return session_data

def set_session_data(key: str, data: str) -> None:
    """Set session data with TTL"""
    mock_redis[key] = {
        "data": data,
        "expires_at": datetime.utcnow().timestamp() + SESSION_TTL,
        "created_at": datetime.utcnow().isoformat()
    }

def cleanup_expired_sessions() -> int:
    """Clean up expired sessions and return count of cleaned sessions"""
    current_time = datetime.utcnow().timestamp()
    expired_keys = []
    
    for key, session_data in mock_redis.items():
        if isinstance(session_data, dict) and "expires_at" in session_data:
            if current_time > session_data["expires_at"]:
                expired_keys.append(key)
    
    for key in expired_keys:
        del mock_redis[key]
    
    return len(expired_keys)

def format_chat_context(chat_history: List[Dict[str, Any]]) -> str:
    """Format chat history into a readable context string"""
    if not chat_history:
        return "No previous conversation context."
    
    context_parts = []
    for msg in chat_history:
        role = "User" if msg["role"] == "user" else "Assistant"
        context_parts.append(f"{role}: {msg['content']}")
    
    return "\n".join(context_parts)
