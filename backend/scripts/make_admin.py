#!/usr/bin/env python3
"""
One-time utility script to grant admin privileges to a user.
Usage: python scripts/make_admin.py <email>
"""

import sys
import os

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlmodel import Session, select
from app.database import engine
from app.models import User


def make_admin(email: str):
    """Grant admin privileges to a user by email."""
    with Session(engine) as session:
        # Find user by email
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()

        if not user:
            print(f"❌ Error: User with email '{email}' not found")
            return False

        if user.is_admin:
            print(f"ℹ️  User '{email}' is already an admin")
            return True

        # Grant admin privileges
        user.is_admin = True
        session.add(user)
        session.commit()
        session.refresh(user)

        print(f"✅ Success: User '{email}' is now an admin")
        print(f"   User ID: {user.id}")
        print(f"   Name: {user.name}")
        print(f"   Admin: {user.is_admin}")
        return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/make_admin.py <email>")
        print("Example: python scripts/make_admin.py admin@example.com")
        sys.exit(1)

    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1)
