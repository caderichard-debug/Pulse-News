from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """Application configuration settings"""

    
    # Database
    database_url: str = "postgresql://postgres:password@db:5432/news_db"
    pulse_access_token: Optional[str] = None

    # API Keys
    openai_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None

    # OAuth Configuration
    google_auth_client_id: Optional[str] = None
    google_auth_client_secret: Optional[str] = None

    # Fact-checking APIs (V2)
    google_fact_check_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None  # For Google Custom Search
    claimbuster_api_key: Optional[str] = None
    # Lightweight PolitiFact/Snopes search HTML (no official API); disable in strict prod if desired
    fact_check_enable_scraping: bool = True
    fact_check_scrape_user_agent: Optional[str] = None

    # Email Configuration
    from_email: str = "newsletter@pulsenews.app"
    from_name: str = "Pulse News"

    # AI Configuration
    ai_model: str = "gpt-4o-mini"  # Cheapest GPT-4 model
    max_tokens_per_request: int = 2000
    batch_size: int = 5  # Process 5 articles per API call
    ai_request_timeout_seconds: int = 45
    ai_max_retries: int = 3

    # Pipeline throughput tuning
    extract_batch_size: int = 50
    analysis_batch_size: int = 5
    framework_batch_size: int = 20
    statistics_batch_size: int = 10
    clustering_batch_size: int = 20
    context_batch_size: int = 5
    pipeline_min_delay_seconds: float = 0.2
    pipeline_max_delay_seconds: float = 2.0
    pipeline_target_error_rate: float = 0.1

    # Resilience defaults
    http_timeout_seconds: int = 10
    http_max_retries: int = 3
    http_backoff_base_seconds: float = 0.5

    # Cost controls
    pipeline_daily_budget_usd: float = 25.0
    pipeline_warn_budget_percent: float = 0.8
    fallback_ai_model: str = "gpt-4o-mini"

    # Application Settings
    secret_key: str = "your-secret-key-change-in-production"
    environment: str = "development"
    debug: bool = True
    frontend_url: str = "http://localhost:3000"
    frontend_custom_url: str = "https://pulsenews.app"
    backend_url: str = "http://localhost:8000"
    auth_url: str = "https://auth.pulsenews.app"  # Dedicated OAuth/auth domain
    enforce_secure_secret_key: bool = True
    auth_rate_limit_window_seconds: int = 60
    auth_rate_limit_max_attempts: int = 15

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

    model_config = {
        # Check for Render secret file first, then fall back to local .env
        "env_file": os.getenv("SECRETS_FILE", ".env"),
        "case_sensitive": False,
        "extra": "ignore"  # Allow extra fields in environment variables
    }


# Create a global settings instance
settings = Settings()
