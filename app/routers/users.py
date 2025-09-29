from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas import UserCreate, UserResponse
from app.crud import create_user, get_user_by_email, get_user_by_id
from app.logging_config import get_logger
from app.config import settings
from slowapi import Limiter
from slowapi.util import get_remote_address

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)
logger = get_logger("users_router")

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
def create_user_endpoint(
    user: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """Create a new user with rate limiting and logging"""
    logger.info("Creating user", email=user.email, client_ip=get_remote_address(request))

    # Check if user already exists
    db_user = get_user_by_email(db, email=user.email)
    if db_user:
        logger.warning("User creation failed - email already exists", email=user.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Validate personality trait (free vs paid)
    trait_validation = validate_personality_trait(user.personality_trait)
    if not trait_validation["is_valid"]:
        logger.warning("User creation failed - invalid personality trait", 
                      email=user.email, trait=user.personality_trait)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=trait_validation["message"]
        )

    try:
        new_user = create_user(db=db, user=user)
        logger.info("User created successfully", 
                   user_id=new_user.id, 
                   email=new_user.email,
                   trait_type=trait_validation["trait_type"])
        return new_user
    except Exception as e:
        logger.error("Error creating user", error=str(e), email=user.email)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )

@router.get("/{user_id}", response_model=UserResponse)
@limiter.limit("30/minute")
def get_user_endpoint(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """Get user by ID with rate limiting and logging"""
    logger.info("Fetching user", user_id=user_id, client_ip=get_remote_address(request))
    
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        logger.warning("User not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
        logger.info("User fetched successfully", user_id=user_id, email=user.email)
        return user

@router.get("/traits/available")
@limiter.limit("30/minute")
def get_available_traits(request: Request):
    """Get available personality traits (free and paid)"""
    logger.info("Getting available traits", client_ip=get_remote_address(request))
    
    free_traits = settings.free_traits.split(",") if settings.free_traits else []
    paid_traits = settings.paid_traits.split(",") if settings.paid_traits else []
    
    traits = {
        "free_traits": [
            {"id": trait.strip(), "name": trait.replace("_", " ").title(), "type": "free"}
            for trait in free_traits
        ],
        "paid_traits": [
            {"id": trait.strip(), "name": trait.replace("_", " ").title(), "type": "paid"}
            for trait in paid_traits
        ],
        "total_traits": len(free_traits) + len(paid_traits)
    }
    
    logger.info("Available traits retrieved", 
                free_count=len(free_traits), 
                paid_count=len(paid_traits))
    
    return traits

@router.get("/traits/validate/{trait}")
@limiter.limit("30/minute")
def validate_trait(trait: str, request: Request):
    """Validate if a personality trait is available and free/paid"""
    logger.info("Validating trait", trait=trait, client_ip=get_remote_address(request))
    
    validation = validate_personality_trait(trait)
    
    return {
        "trait": trait,
        "is_valid": validation["is_valid"],
        "trait_type": validation["trait_type"],
        "message": validation["message"]
    }

def validate_personality_trait(trait: str) -> dict:
    """Validate personality trait and determine if it's free or paid"""
    free_traits = settings.free_traits.split(",") if settings.free_traits else []
    paid_traits = settings.paid_traits.split(",") if settings.paid_traits else []
    
    # Clean trait name
    trait = trait.strip().lower()
    
    # Check if trait is in free traits
    if trait in [t.strip().lower() for t in free_traits]:
        return {
            "is_valid": True,
            "trait_type": "free",
            "message": "Trait is available and free"
        }
    
    # Check if trait is in paid traits
    if trait in [t.strip().lower() for t in paid_traits]:
        return {
            "is_valid": True,
            "trait_type": "paid",
            "message": "Trait is available but requires paid subscription"
        }
    
    # Trait not found
    return {
        "is_valid": False,
        "trait_type": "invalid",
        "message": f"Personality trait '{trait}' is not available. Choose from free traits or upgrade for paid traits."
    }
