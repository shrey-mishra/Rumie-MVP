import os
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database Configuration
    database_url: str = "sqlite:///./rumie.db"
    sqlite_db_path: str = "rumie.db"
    
    # Security Configuration
    secret_key: str = "your_super_secret_key_change_in_production_12345"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # API Configuration
    gemini_api_key: str = "your_gemini_api_key_here"
    api_v1_str: str = "/v1"
    
    # External API Keys
    youtube_api_key: str = "your_youtube_key_here"
    twitch_client_id: str = "your_twitch_client_id_here"
    twitch_client_secret: str = "your_twitch_client_secret_here"
    
    # Personality Traits Configuration
    free_traits: str = "empathetic_mentor,efficient_organizer,analytical_processor"
    paid_traits: str = "creative_thinker,strategic_planner,empathetic_listener"
    
    def validate_gemini_key(self) -> bool:
        """Validate Gemini API key is properly configured"""
        return (
            self.gemini_api_key and 
            self.gemini_api_key != "your_gemini_api_key_here" and
            len(self.gemini_api_key) > 20
        )
    
    def validate_secret_key(self) -> bool:
        """Validate secret key is properly configured"""
        return (
            self.secret_key and 
            self.secret_key != "your_super_secret_key_change_in_production_12345" and
            len(self.secret_key) >= 32
        )
    
    # Rate Limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # CORS Configuration - Restricted to app domains
    allowed_origins: List[str] = ["http://localhost:3000", "https://rumieai.com", "https://app.rumieai.com"]
    allowed_methods: List[str] = ["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    allowed_headers: List[str] = ["Authorization", "Content-Type", "X-Requested-With"]
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    
    # Sentry Configuration
    sentry_dsn: str = "your_sentry_dsn_here"
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()
