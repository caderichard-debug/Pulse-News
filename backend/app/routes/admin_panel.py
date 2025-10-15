"""
Admin panel routes for database management, job monitoring, and system administration.

Security: All endpoints require both valid JWT token AND admin token in headers.
Audit: All actions are logged to AdminAuditLog table.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select, func
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from ..models import (
    User, Article, Source, Topic, Framework, Newsletter,
    ProcessingStatus, JobExecutionHistory, AdminAuditLog
)
from ..database import get_session
from ..utils.admin_auth import get_admin_user, log_admin_action

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin-panel", tags=["admin-panel"])


@router.get("/dashboard")
def get_admin_dashboard(
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard overview for admin panel.

    Returns:
        - System stats (articles, users, sources, jobs)
        - Recent job executions (last 10)
        - Active/running jobs
        - Error summary (failed jobs in last 24h)
        - Recent admin actions (last 10)
    """
    # System stats
    total_users = session.exec(select(func.count(User.id))).first()
    admin_users = session.exec(
        select(func.count(User.id)).where(User.is_admin == True)
    ).first()

    total_articles = session.exec(select(func.count(Article.id))).first()
    articles_today = session.exec(
        select(func.count(Article.id))
        .where(Article.scraped_at >= datetime.utcnow() - timedelta(days=1))
    ).first()

    total_sources = session.exec(select(func.count(Source.id))).first()
    active_sources = session.exec(
        select(func.count(Source.id)).where(Source.is_active == True)
    ).first()

    total_frameworks = session.exec(select(func.count(Framework.id))).first()

    # Recent job executions (last 10)
    recent_jobs = session.exec(
        select(JobExecutionHistory)
        .order_by(JobExecutionHistory.started_at.desc())
        .limit(10)
    ).all()

    recent_jobs_data = [
        {
            "id": job.id,
            "job_id": job.job_id,
            "job_name": job.job_name,
            "status": job.status,
            "started_at": job.started_at.isoformat(),
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "duration_seconds": job.duration_seconds,
            "items_processed": job.items_processed,
            "error_message": job.error_message
        }
        for job in recent_jobs
    ]

    # Active/running jobs
    active_jobs = session.exec(
        select(JobExecutionHistory)
        .where(JobExecutionHistory.status == "running")
    ).all()

    active_jobs_data = [
        {
            "id": job.id,
            "job_id": job.job_id,
            "job_name": job.job_name,
            "started_at": job.started_at.isoformat(),
            "duration_seconds": (datetime.utcnow() - job.started_at).total_seconds()
        }
        for job in active_jobs
    ]

    # Error summary (failed jobs in last 24h)
    yesterday = datetime.utcnow() - timedelta(days=1)
    failed_jobs_24h = session.exec(
        select(func.count(JobExecutionHistory.id))
        .where(JobExecutionHistory.status == "failed")
        .where(JobExecutionHistory.started_at >= yesterday)
    ).first()

    # Recent admin actions (last 10)
    recent_actions = session.exec(
        select(AdminAuditLog)
        .order_by(AdminAuditLog.timestamp.desc())
        .limit(10)
    ).all()

    recent_actions_data = [
        {
            "id": action.id,
            "admin_email": action.admin_email,
            "action_type": action.action_type,
            "resource_type": action.resource_type,
            "resource_id": action.resource_id,
            "timestamp": action.timestamp.isoformat()
        }
        for action in recent_actions
    ]

    return {
        "system_stats": {
            "users": {
                "total": total_users,
                "admins": admin_users
            },
            "articles": {
                "total": total_articles,
                "today": articles_today
            },
            "sources": {
                "total": total_sources,
                "active": active_sources
            },
            "frameworks": {
                "total": total_frameworks
            }
        },
        "recent_jobs": recent_jobs_data,
        "active_jobs": active_jobs_data,
        "error_summary": {
            "failed_jobs_24h": failed_jobs_24h
        },
        "recent_admin_actions": recent_actions_data,
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/verify")
def verify_admin_access(
    admin_user: User = Depends(get_admin_user)
) -> Dict[str, Any]:
    """
    Verify admin token and user permissions.
    Used by frontend to validate admin access.
    """
    return {
        "valid": True,
        "user": {
            "id": admin_user.id,
            "email": admin_user.email,
            "name": admin_user.name,
            "is_admin": admin_user.is_admin
        }
    }
