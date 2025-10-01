from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # Database
    database_url: str = "postgresql://postgres:password@db:5432/news_db"

    # API Keys
    openai_api_key: Optional[str] = None
    resend_api_key: Optional[str] = None

    # Email Configuration
    from_email: str = "newsletter@pulse.news"
    from_name: str = "Pulse News"

    # AI Configuration
    ai_model: str = "gpt-4o-mini"  # Cheapest GPT-4 model
    max_tokens_per_request: int = 2000
    batch_size: int = 5  # Process 5 articles per API call

    # Application Settings
    secret_key: str = "your-secret-key-change-in-production"
    environment: str = "development"
    debug: bool = True

    # Scraping Configuration
    scrape_interval_hours: int = 3
    process_interval_hours: int = 4
    max_articles_per_source: int = 10  # Limit articles per scrape

    # Newsletter Configuration
    newsletter_send_hour: int = 7  # 7 AM
    max_articles_per_newsletter: int = 5
    max_frameworks_per_newsletter: int = 3

    class Config:
        env_file = ".env"
        case_sensitive = False


# Create a global settings instance
settings = Settings()
