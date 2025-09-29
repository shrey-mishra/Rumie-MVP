from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.dependencies import get_db, get_redis
from app.crud import get_user_by_email, create_user
from app.schemas import UserCreate
from app.auth import authenticate_user, create_access_token, get_current_user, get_password_hash, verify_password
from app.logging_config import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address
from datetime import timedelta
import time
from app.config import settings
from pydantic import BaseModel
from typing import Optional

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("auth_router")

class Token(BaseModel):
    access_token: str
    token_type: str
    expires_in: int

class UserLogin(BaseModel):
    email: str
    password: str

class UserRegister(BaseModel):
    email: str
    password: str
    mode_pref: str
    personality_trait: str

@router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    request: Request = None,
    db: Session = Depends(get_db)
):
    """Login endpoint for JWT token generation"""
    logger.info("Login attempt", email=form_data.username, client_ip=get_remote_address(request))
    
    # For demo purposes, create a user if they don't exist
    user = get_user_by_email(db, email=form_data.username)
    if not user:
        # Create a demo user with hashed password
        user_data = UserCreate(
            email=form_data.username,
            mode_pref="work",
            personality_trait="efficient_organizer"
        )
        user = create_user(db=db, user=user_data)
        # Set hashed password for demo
        user.hashed_password = get_password_hash(form_data.password or "demo123")
        db.commit()
        db.refresh(user)
    
    # Authenticate user
    user = authenticate_user(db, form_data.username, form_data.password or "demo123")
    if not user:
        logger.warning("Login failed - invalid credentials", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    logger.info("Login successful", user_id=user.id, email=user.email)
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@router.post("/register", response_model=Token)
@limiter.limit("5/minute")
async def register_user(
    user_data: UserRegister,
    request: Request,
    db: Session = Depends(get_db)
):
    """Register a new user and return JWT token"""
    logger.info("User registration attempt", email=user_data.email, client_ip=get_remote_address(request))
    
    # Check if user already exists
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        logger.warning("Registration failed - email already exists", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    try:
        from app.schemas import UserCreate
        create_data = UserCreate(
            email=user_data.email,
            mode_pref=user_data.mode_pref,
            personality_trait=user_data.personality_trait
        )
        user = create_user(db=db, user=create_data)
        
        # Set hashed password
        user.hashed_password = get_password_hash(user_data.password)
        db.commit()
        db.refresh(user)
        
        # Generate JWT token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)}, expires_delta=access_token_expires
        )
        
        logger.info("User registration successful", user_id=user.id, email=user.email)
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": settings.access_token_expire_minutes * 60
        }
        
    except Exception as e:
        logger.error("Error during user registration", error=str(e), email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

@router.get("/me")
@limiter.limit("30/minute")
async def get_current_user_info(
    current_user = Depends(get_current_user),
    request: Request = None
):
    """Get current user information"""
    logger.info("User info request", user_id=current_user.id, client_ip=get_remote_address(request))
    
    return {
        "id": current_user.id,
        "email": current_user.email,
        "mode_pref": current_user.mode_pref,
        "personality_trait": current_user.personality_trait,
        "is_paid": current_user.is_paid,
        "created_at": current_user.created_at.isoformat() if current_user.created_at else None
    }

@router.post("/refresh")
@limiter.limit("10/minute")
async def refresh_token(
    current_user = Depends(get_current_user),
    request: Request = None
):
    """Refresh JWT token"""
    logger.info("Token refresh request", user_id=current_user.id, client_ip=get_remote_address(request))
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(current_user.id)}, expires_delta=access_token_expires
    )
    
    logger.info("Token refreshed", user_id=current_user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60
    }

@router.post("/logout")
@limiter.limit("10/minute")
async def logout(
    current_user = Depends(get_current_user),
    request: Request = None,
    redis_client = Depends(get_redis)
):
    """Logout user with token blacklisting"""
    logger.info("User logout", user_id=current_user.id, client_ip=get_remote_address(request))
    
    # Get the token from the request headers
    from fastapi.security import HTTPBearer
    from fastapi import Header
    
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            # Blacklist the token in Redis with 1-hour expiry
            redis_client.setex(f"blacklist:{token}", 3600, "true")
            logger.info("Token blacklisted", user_id=current_user.id, token=token[:10] + "...")
            
            return {
                "message": "Successfully logged out",
                "user_id": current_user.id,
                "token_blacklisted": True
            }
        else:
            logger.warning("No valid token found for logout", user_id=current_user.id)
            return {
                "message": "Logged out (no token found)",
                "user_id": current_user.id,
                "token_blacklisted": False
            }
    except Exception as e:
        logger.error("Error during logout", user_id=current_user.id, error=str(e))
        return {
            "message": "Logged out (blacklist failed)",
            "user_id": current_user.id,
            "token_blacklisted": False
        }

@router.post("/reset-password")
@limiter.limit("5/minute")
async def reset_password(
    email: str,
    request: Request = None
):
    """Request password reset (mock implementation)"""
    logger.info("Password reset requested", email=email, client_ip=get_remote_address(request))
    
    # Mock email sending (in production, use real email service)
    reset_token = f"reset_{int(time.time())}_{hash(email)}"
    
    # Store reset token in Redis with 1-hour expiry (mock)
    logger.info("Password reset token generated", 
               email=email, 
               token=reset_token[:10] + "...")
    
    return {
        "message": "Password reset link sent to your email",
        "status": "success",
        "email": email
    }

@router.post("/confirm-reset")
@limiter.limit("5/minute")
async def confirm_password_reset(
    token: str,
    new_password: str,
    request: Request = None
):
    """Confirm password reset with token"""
    logger.info("Password reset confirmation", 
               token=token[:10] + "...", 
               client_ip=get_remote_address(request))
    
    # Mock token validation (in production, validate against stored token)
    if not token.startswith("reset_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid reset token"
        )
    
    # Mock password update (in production, update user password)
    logger.info("Password reset completed", token=token[:10] + "...")
    
    return {
        "message": "Password successfully reset",
        "status": "success"
    }
