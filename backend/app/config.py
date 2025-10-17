from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""
    
    # Admin
    admin_token: Optional[str] = None

    # Database
    database_url: str = "postgresql://postgres:password@db:5432/news_db"
    pulse_access_token: Optional[str] = None

    # API Keys
    openai_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None

    # Fact-checking APIs (V2)
    google_fact_check_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None  # For Google Custom Search
    claimbuster_api_key: Optional[str] = None

    # Email Configuration
    from_email: str = "newsletter@pulsenews.app"
    from_name: str = "Pulse News"

    # AI Configuration
    ai_model: str = "gpt-4o-mini"  # Cheapest GPT-4 model
    max_tokens_per_request: int = 2000
    batch_size: int = 5  # Process 5 articles per API call

    # Application Settings
    secret_key: str = "your-secret-key-change-in-production"
    environment: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:3000"
    backend_url: str = "http://localhost:8000"

    # Scraping Configuration
    scrape_interval_hours: int = 3
    process_interval_hours: int = 4
    max_articles_per_source: int = 10  # Limit articles per scrape

    # Newsletter Configuration
    newsletter_send_hour: int = 7  # 7 AM
    max_articles_per_newsletter: int = 5
    max_frameworks_per_newsletter: int = 3

    # Admin Panel Configuration
    admin_token: Optional[str] = None
    admin_panel_enabled: bool = True
    max_audit_log_days: int = 90  # Keep audit logs for 90 days
    max_job_history_days: int = 30  # Keep job history for 30 days
    admin_token_rotation_days: int = 90  # Rotate admin token every 90 days

    class Config:
        # Check for Render secret file first, then fall back to local .env
        env_file = os.getenv("SECRETS_FILE", ".env")
        case_sensitive = False


# Create a global settings instance
settings = Settings()
