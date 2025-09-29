from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.crud import get_user_by_id
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import uuid

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("voice_router")

# Mock storage for voice data
voice_data = {}

class VoiceRequest(BaseModel):
    text: str
    voice_type: str = "natural"  # natural, professional, friendly
    speed: float = 1.0  # 0.5 to 2.0
    language: str = "en-US"

class VoiceResponse(BaseModel):
    audio_url: str
    duration_seconds: float
    voice_type: str
    text_length: int
    processing_time_ms: int

class VoiceSession(BaseModel):
    session_id: str
    user_id: int
    text: str
    voice_type: str
    created_at: str
    audio_url: str
    duration_seconds: float

@router.post("/synthesize/{user_id}", response_model=VoiceResponse)
@limiter.limit("5/minute")
def synthesize_speech(
    user_id: int,
    voice_request: VoiceRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Synthesize speech from text (Paid Feature)"""
    logger.info(
        "Voice synthesis request", 
        user_id=user_id, 
        text_length=len(voice_request.text),
        voice_type=voice_request.voice_type,
        client_ip=get_remote_address(request)
    )
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice synthesis failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if user has paid access (mock implementation)
    if not check_voice_access(user_id):
        logger.warning("Voice synthesis failed - no paid access", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Voice synthesis is a paid feature. Please upgrade your plan."
        )
    
    # Mock voice synthesis
    session_id = str(uuid.uuid4())
    audio_url = f"https://api.rumieai.com/voice/{session_id}.mp3"
    
    # Calculate duration based on text length and speed
    words_per_minute = 150 * voice_request.speed
    duration_seconds = (len(voice_request.text.split()) / words_per_minute) * 60
    
    # Store voice session
    voice_session = {
        "session_id": session_id,
        "user_id": user_id,
        "text": voice_request.text,
        "voice_type": voice_request.voice_type,
        "created_at": datetime.utcnow().isoformat(),
        "audio_url": audio_url,
        "duration_seconds": duration_seconds
    }
    
    voice_data[session_id] = voice_session
    
    # Mock processing time
    processing_time_ms = int(len(voice_request.text) * 10)  # 10ms per character
    
    logger.info(
        "Voice synthesis completed", 
        user_id=user_id, 
        session_id=session_id,
        duration_seconds=duration_seconds
    )
    
    return VoiceResponse(
        audio_url=audio_url,
        duration_seconds=duration_seconds,
        voice_type=voice_request.voice_type,
        text_length=len(voice_request.text),
        processing_time_ms=processing_time_ms
    )

@router.get("/sessions/{user_id}")
@limiter.limit("20/minute")
def get_voice_sessions(
    user_id: int,
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's voice synthesis sessions"""
    logger.info("Getting voice sessions", user_id=user_id, limit=limit, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice sessions failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's voice sessions
    user_sessions = [
        session for session in voice_data.values() 
        if session.get("user_id") == user_id
    ]
    
    # Sort by creation time (newest first)
    user_sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit results
    user_sessions = user_sessions[:limit]
    
    logger.info("Voice sessions retrieved", user_id=user_id, session_count=len(user_sessions))
    
    return {
        "user_id": user_id,
        "sessions": user_sessions,
        "total_sessions": len(user_sessions),
        "limit": limit
    }

@router.get("/access/{user_id}")
@limiter.limit("10/minute")
def check_voice_access_status(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Check if user has voice synthesis access"""
    logger.info("Checking voice access", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice access check failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    has_access = check_voice_access(user_id)
    
    return {
        "user_id": user_id,
        "has_voice_access": has_access,
        "feature": "voice_synthesis",
        "plan_required": "premium" if not has_access else "current",
        "upgrade_url": "https://rumieai.com/upgrade" if not has_access else None
    }

@router.get("/voices/available")
@limiter.limit("30/minute")
def get_available_voices(request: Request):
    """Get list of available voice types"""
    logger.info("Getting available voices", client_ip=get_remote_address(request))
    
    voices = [
        {
            "id": "natural",
            "name": "Natural Voice",
            "description": "Warm and conversational",
            "language": "en-US",
            "gender": "neutral",
            "premium": False
        },
        {
            "id": "professional",
            "name": "Professional Voice",
            "description": "Clear and authoritative",
            "language": "en-US",
            "gender": "male",
            "premium": True
        },
        {
            "id": "friendly",
            "name": "Friendly Voice",
            "description": "Cheerful and approachable",
            "language": "en-US",
            "gender": "female",
            "premium": True
        },
        {
            "id": "analytical",
            "name": "Analytical Voice",
            "description": "Precise and methodical",
            "language": "en-US",
            "gender": "neutral",
            "premium": True
        }
    ]
    
    return {
        "voices": voices,
        "total_voices": len(voices),
        "premium_voices": len([v for v in voices if v["premium"]])
    }

def check_voice_access(user_id: int) -> bool:
    """Check if user has paid access to voice features (mock implementation)"""
    # Mock implementation - in production, this would check user's subscription
    # For demo purposes, assume users with ID > 10 have premium access
    return user_id > 10

@router.delete("/session/{session_id}")
@limiter.limit("10/minute")
def delete_voice_session(
    session_id: str,
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Delete a voice synthesis session"""
    logger.info("Deleting voice session", session_id=session_id, user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice session deletion failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if session exists and belongs to user
    if session_id not in voice_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Voice session not found"
        )
    
    session = voice_data[session_id]
    if session.get("user_id") != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this voice session"
        )
    
    # Delete session
    del voice_data[session_id]
    
    logger.info("Voice session deleted", session_id=session_id, user_id=user_id)
    
    return {
        "status": "deleted",
        "session_id": session_id,
        "user_id": user_id
    }

@router.post("/command/{user_id}")
@limiter.limit("10/minute")
async def process_voice_command(
    user_id: int,
    audio_transcript: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """Process voice command with Gemini analysis"""
    logger.info("Processing voice command", user_id=user_id, transcript_length=len(audio_transcript), client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice command failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Create prompt for Gemini to process voice command
        prompt = f"""
        Process this voice command and provide a helpful response:
        
        Voice Transcript: "{audio_transcript}"
        
        User Profile:
        - Personality: {user.personality_trait}
        - Mode Preference: {user.mode_pref}
        
        Instructions:
        1. Understand the user's intent from the voice command
        2. Provide a helpful, personalized response
        3. If it's a task request, suggest specific actions
        4. If it's a question, provide a clear answer
        5. Adapt your response to their personality and mode preference
        6. Keep the response concise but comprehensive
        """
        
        # Get AI response using Gemini service
        from app.services.gemini_service import gemini_service
        ai_response = await gemini_service.generate_empathetic_response(
            user_input=prompt,
            user_personality=user.personality_trait,
            mode_pref=user.mode_pref
        )
        
        # Store voice command for history
        command_id = str(uuid.uuid4())
        voice_data[f"command:{command_id}"] = {
            "command_id": command_id,
            "user_id": user_id,
            "transcript": audio_transcript,
            "response": ai_response["response"],
            "confidence": ai_response["confidence"],
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Voice command processed", user_id=user_id, command_id=command_id, confidence=ai_response["confidence"])
        
        return {
            "command_id": command_id,
            "user_id": user_id,
            "transcript": audio_transcript,
            "response": ai_response["response"],
            "confidence": ai_response["confidence"],
            "emotion": ai_response["emotion"],
            "personality_match": ai_response.get("personality_match", user.personality_trait),
            "mode_adapted": ai_response.get("mode_adapted", user.mode_pref),
            "processed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error processing voice command", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process voice command"
        )

@router.get("/commands/{user_id}")
@limiter.limit("20/minute")
def get_voice_commands(
    user_id: int,
    request: Request,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get user's voice command history"""
    logger.info("Getting voice commands", user_id=user_id, limit=limit, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Voice commands request failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Get user's voice commands
    user_commands = []
    for key, command in voice_data.items():
        if key.startswith(f"command:") and command.get("user_id") == user_id:
            user_commands.append(command)
    
    # Sort by creation time (newest first)
    user_commands.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    
    # Limit results
    user_commands = user_commands[:limit]
    
    logger.info("Voice commands retrieved", user_id=user_id, command_count=len(user_commands))
    
    return {
        "user_id": user_id,
        "commands": user_commands,
        "total_commands": len(user_commands),
        "limit": limit
    }

@router.post("/transcribe/{user_id}")
@limiter.limit("5/minute")
async def transcribe_audio(
    user_id: int,
    audio_data: dict,  # Mock audio data
    request: Request,
    db: Session = Depends(get_db)
):
    """Transcribe audio to text (mock implementation)"""
    logger.info("Transcribing audio", user_id=user_id, client_ip=get_remote_address(request))
    
    # Verify user exists
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("Audio transcription failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    try:
        # Mock transcription (in production, use real speech-to-text API)
        mock_transcript = "Hello, I need help with my daily tasks and productivity planning"
        
        # Store transcription
        transcription_id = str(uuid.uuid4())
        voice_data[f"transcription:{transcription_id}"] = {
            "transcription_id": transcription_id,
            "user_id": user_id,
            "transcript": mock_transcript,
            "confidence": 0.95,
            "language": "en-US",
            "duration_seconds": audio_data.get("duration", 5.0),
            "created_at": datetime.utcnow().isoformat()
        }
        
        logger.info("Audio transcribed", user_id=user_id, transcription_id=transcription_id)
        
        return {
            "transcription_id": transcription_id,
            "user_id": user_id,
            "transcript": mock_transcript,
            "confidence": 0.95,
            "language": "en-US",
            "duration_seconds": audio_data.get("duration", 5.0),
            "transcribed_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error("Error transcribing audio", error=str(e), user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to transcribe audio"
        )
