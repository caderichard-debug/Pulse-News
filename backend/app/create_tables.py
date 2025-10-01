"""
Simple script to create all database tables.
Run this before seeding data.
"""

from sqlmodel import SQLModel
from app.database import engine
from app.models import (
    Source,
    Topic,
    Article,
    ArticleAnalysis,
    Framework,
    User,
    Newsletter,
    SourceTopicLink,
    ArticleFrameworkLink,
    UserTopicPreference,
)

print("Creating all database tables...")
SQLModel.metadata.create_all(engine)
print("✅ Tables created successfully!")
