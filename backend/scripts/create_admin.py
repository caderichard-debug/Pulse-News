"""
Script to grant admin privileges to a user.

Usage (from container):
    docker-compose exec backend python scripts/create_admin.py user@example.com

Usage (from local):
    python -m backend.scripts.create_admin user@example.com
"""
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlmodel import Session, select
from app.database import engine
from app.models import User


def make_admin(email: str):
    """Grant admin privileges to user."""
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == email)).first()

        if not user:
            print(f"✗ User '{email}' not found")
            print("\nAvailable users:")
            users = session.exec(select(User)).all()
            for u in users:
                admin_badge = " (ADMIN)" if u.is_admin else ""
                print(f"  - {u.email}{admin_badge}")
            return False

        if user.is_admin:
            print(f"✓ {email} is already an admin")
            return True

        user.is_admin = True
        session.add(user)
        session.commit()

        print(f"✓ {email} is now an admin")
        return True


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: docker-compose exec backend python scripts/create_admin.py user@example.com")
        sys.exit(1)

    email = sys.argv[1]
    success = make_admin(email)
    sys.exit(0 if success else 1)
