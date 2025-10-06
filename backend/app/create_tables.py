"""
Simple script to create all database tables.
Run this before seeding data.
"""

from sqlmodel import SQLModel
from .database import engine
from .models import (
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
