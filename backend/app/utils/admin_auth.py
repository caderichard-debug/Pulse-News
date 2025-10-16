"""
Admin authentication utilities.
Validates admin token and user permissions.
"""
from fastapi import HTTPException, status, Depends, Header, Request
from typing import Optional
from ..config import settings
from ..routes.auth import get_current_user
from ..models import User, AdminAuditLog
from sqlmodel import Session
from ..database import get_session
import logging

logger = logging.getLogger(__name__)


def verify_admin_token(x_admin_token: Optional[str] = Header(None)) -> bool:
    """
    Verify admin token from request headers.
    Raises HTTPException if invalid.
    """
    if not settings.admin_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin token not configured on server"
        )

    if not x_admin_token or x_admin_token != settings.admin_token:
        logger.warning("Invalid admin token attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token"
        )

    return True


def get_admin_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and verify they have admin privileges.
    Requires valid JWT token and user must have is_admin=True.
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.email} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


def get_admin_user_with_token(
    current_user: User = Depends(get_current_user),
    _: bool = Depends(verify_admin_token)
) -> User:
    """
    Get current user and verify they have admin privileges.
    Requires both valid JWT token AND admin token (for extra sensitive operations).
    """
    if not current_user.is_admin:
        logger.warning(f"Non-admin user {current_user.email} attempted admin access")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return current_user


def log_admin_action(
    admin_user: User,
    action_type: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    old_value: Optional[str] = None,
    new_value: Optional[str] = None,
    session: Session = None,
    request: Request = None
):
    """
    Create an audit log entry for an admin action.

    Args:
        admin_user: The admin User object
        action_type: Type of action (e.g., 'delete_article', 'trigger_job')
        resource_type: Type of resource (e.g., 'article', 'user', 'job')
        resource_id: ID of the resource (optional)
        old_value: JSON string of old value (optional)
        new_value: JSON string of new value (optional)
        session: Database session (creates new if None)
        request: FastAPI Request object for IP/user agent
    """
    if session is None:
        from ..database import engine
        with Session(engine) as db:
            _create_audit_log(admin_user, action_type, resource_type,
                            resource_id, old_value, new_value, db, request)
    else:
        _create_audit_log(admin_user, action_type, resource_type,
                        resource_id, old_value, new_value, session, request)


def _create_audit_log(admin_user, action_type, resource_type, resource_id,
                      old_value, new_value, session, request):
    """Helper to create audit log."""
    # Extract IP and user agent safely
    ip_address = None
    user_agent = None
    if request:
        try:
            ip_address = request.client.host if hasattr(request, 'client') and request.client else None
            user_agent = request.headers.get("user-agent") if hasattr(request, 'headers') else None
        except AttributeError:
            pass

    audit = AdminAuditLog(
        user_id=admin_user.id,
        admin_email=admin_user.email,
        action_type=action_type,
        resource_type=resource_type,
        resource_id=resource_id,
        old_value=old_value,
        new_value=new_value,
        ip_address=ip_address,
        user_agent=user_agent
    )
    session.add(audit)
    session.commit()

    logger.info(
        f"Admin action logged: {admin_user.email} - {action_type} on "
        f"{resource_type} {resource_id or '(no ID)'}"
    )
