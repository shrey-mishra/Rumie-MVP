from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.config import settings
from app.models import Base
import redis
from typing import Generator

# Create database engine
engine = create_engine(
    settings.database_url, 
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Redis client
redis_client = redis.from_url(settings.redis_url, decode_responses=True)

def get_db() -> Session:
    """
    Dependency to get database session
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_redis():
    """
    Dependency to get Redis client
    """
    try:
        yield redis_client
    except Exception as e:
        # Fallback to mock Redis if real Redis fails
        from app.routers.chat import mock_redis
        yield mock_redis

def create_tables():
    """
    Create all database tables
    """
    Base.metadata.create_all(bind=engine)
