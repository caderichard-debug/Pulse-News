#!/usr/bin/env python3
"""
Simple script to test a database connection using SQLAlchemy.
Works for PostgreSQL, MySQL, SQLite, etc. — just set DATABASE_URL accordingly.
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# --- 1. Get database URL from environment variable ---
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db:5432/news_db")

if not DATABASE_URL:
    print("❌ Error: DATABASE_URL environment variable is not set.")
    sys.exit(1)

# --- 2. Create the engine (does not connect yet) ---
print(f"🔧 Testing database connection to: {DATABASE_URL}")
engine = create_engine(DATABASE_URL, echo=True)  # echo=True prints SQL

# --- 3. Try to connect and run a simple query ---
try:
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1")).scalar()
        if result == 1:
            print("✅ Successfully connected to the database and executed SELECT 1.")
        else:
            print("⚠️ Unexpected result from SELECT 1:", result)
except SQLAlchemyError as e:
    print("❌ Database connection test failed.")
    print("Error details:", e)
    sys.exit(1)
