from fastapi import FastAPI, Request, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from app.auth import authenticate_user, create_access_token, get_current_user, require_paid_access
from app.crud import get_user_by_email
from app.schemas import UserCreate
from pydantic import BaseModel
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.dependencies import create_tables, get_db, get_redis
from app.routers import users, ai, integrations, mom, chat, productivity, voice, analytics, campaign, auth, monitoring
from app.config import settings
from app.logging_config import get_logger
import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration

# Create database tables
create_tables()

# Initialize logger
logger = get_logger("main")

# Initialize Sentry monitoring (only if DSN is valid)
if settings.sentry_dsn and settings.sentry_dsn != "your_sentry_dsn_here" and settings.sentry_dsn != "mock_sentry_dsn":
    try:
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            integrations=[
                FastApiIntegration(),
                SqlalchemyIntegration(),
            ],
            traces_sample_rate=1.0,
            environment=settings.environment,
            debug=settings.debug,
        )
        logger.info("Sentry monitoring initialized")
    except Exception as e:
        logger.warning("Sentry initialization failed", error=str(e))
        logger.info("Falling back to structured logging for error tracking")
else:
    logger.info("Sentry monitoring disabled - using structured logging fallback")
    logger.info("To enable Sentry, set SENTRY_DSN environment variable")
    
    # Initialize mock Sentry for error tracking
    from app.services.mock_sentry import mock_sentry
    logger.info("Mock Sentry service initialized for error tracking")

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# OAuth2 scheme for authentication (placeholder for Phase II)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI(
    title="RumieAI API",
    description="AI-powered personal assistant API with empathetic responses",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Include routers
app.include_router(auth.router, prefix="/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/v1/users", tags=["users"])
app.include_router(ai.router, prefix="/v1/ai", tags=["ai"])
app.include_router(integrations.router, prefix="/v1/integrations", tags=["integrations"])
app.include_router(mom.router, prefix="/v1/mom", tags=["mom"])
app.include_router(chat.router, prefix="/v1/chat", tags=["chat"])
app.include_router(productivity.router, prefix="/v1/productivity", tags=["productivity"])
app.include_router(voice.router, prefix="/v1/voice", tags=["voice"])
app.include_router(analytics.router, prefix="/v1/analytics", tags=["analytics"])
app.include_router(campaign.router, prefix="/v1/campaign", tags=["campaign"])
app.include_router(monitoring.router, prefix="/v1/monitoring", tags=["monitoring"])

@app.get("/")
@limiter.limit("10/minute")
async def read_root(request: Request):
    logger.info("Root endpoint accessed", client_ip=get_remote_address(request))
    return {"message": "Welcome to RumieAI API", "version": "1.0.0"}

@app.get("/health")
@limiter.limit("30/minute")
async def health_check(request: Request, redis_client = Depends(get_redis)):
    logger.info("Health check accessed", client_ip=get_remote_address(request))
    
    health_status = {
        "status": "healthy",
        "environment": settings.environment,
        "version": "1.0.0",
        "services": {}
    }
    
    # Check Redis
    try:
        redis_client.ping()
        health_status["services"]["redis"] = "healthy"
    except Exception as e:
        health_status["services"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check Gemini API
    try:
        from app.services.gemini_service import gemini_service
        test_response = await gemini_service.generate_empathetic_response(
            user_input="Health check ping",
            user_personality="efficient_organizer",
            mode_pref="work"
        )
        health_status["services"]["gemini"] = "healthy"
    except Exception as e:
        health_status["services"]["gemini"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    # Check database
    try:
        from app.dependencies import get_db
        db = next(get_db())
        db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    logger.info("Health check completed", 
               status=health_status["status"],
               services=health_status["services"])
    
    return health_status

