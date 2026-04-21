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
from ..jobs.scheduler import list_scheduler_jobs, control_scheduler_job

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


# ============================================================================
# JOB MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/jobs/history")
def get_job_history(
    job_id: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get job execution history with optional filtering.

    Args:
        job_id: Filter by specific job ID (e.g., 'scrape_rss')
        status: Filter by status (success, failed, running)
        limit: Max results to return (default 50)
        offset: Pagination offset

    Returns:
        List of job execution records with pagination info
    """
    query = select(JobExecutionHistory)

    if job_id:
        query = query.where(JobExecutionHistory.job_id == job_id)
    if status:
        query = query.where(JobExecutionHistory.status == status)

    query = query.order_by(JobExecutionHistory.started_at.desc())

    # Get total count
    count_query = select(func.count(JobExecutionHistory.id))
    if job_id:
        count_query = count_query.where(JobExecutionHistory.job_id == job_id)
    if status:
        count_query = count_query.where(JobExecutionHistory.status == status)
    total_count = session.exec(count_query).first()

    # Get paginated results
    jobs = session.exec(query.limit(limit).offset(offset)).all()

    return {
        "jobs": [
            {
                "id": job.id,
                "job_id": job.job_id,
                "job_name": job.job_name,
                "status": job.status,
                "started_at": job.started_at.isoformat(),
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                "duration_seconds": job.duration_seconds,
                "items_processed": job.items_processed,
                "api_calls_made": job.api_calls_made,
                "tokens_used": job.tokens_used,
                "triggered_by": job.triggered_by,
                "error_message": job.error_message
            }
            for job in jobs
        ],
        "total_count": total_count,
        "limit": limit,
        "offset": offset
    }


@router.get("/jobs/history/{execution_id}")
def get_job_execution_log(
    execution_id: int,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """Get detailed log payload for a single job execution."""
    job = session.get(JobExecutionHistory, execution_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job execution not found",
        )

    return {
        "id": job.id,
        "job_id": job.job_id,
        "job_name": job.job_name,
        "status": job.status,
        "started_at": job.started_at.isoformat(),
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "duration_seconds": job.duration_seconds,
        "items_processed": job.items_processed,
        "api_calls_made": job.api_calls_made,
        "tokens_used": job.tokens_used,
        "triggered_by": job.triggered_by,
        "triggered_by_user_id": job.triggered_by_user_id,
        "error_message": job.error_message,
        "result_data": job.result_data,
    }


@router.get("/jobs/scheduler")
def get_scheduler_jobs(
    admin_user: User = Depends(get_admin_user),
) -> Dict[str, Any]:
    """Get scheduler definitions with pause/schedule state."""
    return list_scheduler_jobs()


@router.post("/jobs/control/{job_id}")
def control_job_schedule(
    job_id: str,
    action: str,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session),
) -> Dict[str, Any]:
    """
    Control a scheduler job:
    - pause: temporarily disable schedule
    - resume: re-enable schedule
    - stop: alias of pause
    - trigger: queue immediate run
    """
    action = action.lower().strip()
    if action not in {"pause", "resume", "stop", "trigger"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid action. Supported actions: pause, resume, stop, trigger",
        )

    result = control_scheduler_job(job_id, action)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Failed to control job"),
        )

    log_admin_action(
        admin_user=admin_user,
        action_type=f"control_job_{action}",
        resource_type="scheduler_job",
        resource_id=job_id,
        new_value=str(result),
        session=session,
        request=request,
    )
    return result


@router.post("/jobs/trigger/{job_id}")
def trigger_job(
    job_id: str,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Trigger a one-off background job execution.

    Valid job_ids:
        - scrape_rss
        - extract_articles
        - analyze_articles
        - reanalyze_unanalyzed_failed
        - update_frameworks
        - verify_statistics
        - cluster_articles
        - generate_context
        - send_newsletters

    Note: Does not modify permanent schedule, only triggers one execution.
    """
    from ..jobs.tasks import (
        scrape_job, extract_job, analyze_job, framework_job,
        statistics_verification_job, article_clustering_job,
        context_generation_job, newsletter_job, reanalyze_unanalyzed_failed_job
    )

    # Map job IDs to functions
    job_map = {
        "scrape_rss": ("scrape_job", scrape_job, "Scrape RSS Feeds"),
        "extract_articles": ("extract_job", extract_job, "Extract Article Content"),
        "analyze_articles": ("analyze_job", analyze_job, "AI Article Analysis"),
        "reanalyze_unanalyzed_failed": (
            "reanalyze_unanalyzed_failed_job",
            reanalyze_unanalyzed_failed_job,
            "Re-analyze Unanalyzed/Failed Articles",
        ),
        "update_frameworks": ("framework_job", framework_job, "Update Frameworks"),
        "verify_statistics": ("statistics_verification_job", statistics_verification_job, "Verify Statistics"),
        "cluster_articles": ("article_clustering_job", article_clustering_job, "Cluster Articles"),
        "generate_context": ("context_generation_job", context_generation_job, "Generate Context"),
        "send_newsletters": ("newsletter_job", newsletter_job, "Send Daily Newsletters")
    }

    if job_id not in job_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid job_id. Valid options: {', '.join(job_map.keys())}"
        )

    job_func_name, job_func, job_name = job_map[job_id]

    # Create job execution history record
    job_history = JobExecutionHistory(
        job_id=job_id,
        job_name=job_name,
        started_at=datetime.utcnow(),
        status="running",
        triggered_by="admin",
        triggered_by_user_id=admin_user.id
    )
    session.add(job_history)
    session.commit()
    session.refresh(job_history)

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="trigger_job",
        resource_type="job",
        resource_id=job_id,
        session=session,
        request=request
    )

    # Execute job and update history
    try:
        result = job_func(session=session)

        job_history.status = "success" if result.get("success", True) else "failed"
        job_history.completed_at = datetime.utcnow()
        job_history.duration_seconds = (
            job_history.completed_at - job_history.started_at
        ).total_seconds()
        job_history.result_data = str(result)

        # Extract metrics if available
        if isinstance(result, dict):
            job_history.items_processed = (
                result.get("articles_scraped") or
                result.get("articles_processed") or
                result.get("articles_analyzed") or
                result.get("mappings_created")
            )
            job_history.tokens_used = result.get("tokens_used")

    except Exception as e:
        job_history.status = "failed"
        job_history.completed_at = datetime.utcnow()
        job_history.duration_seconds = (
            job_history.completed_at - job_history.started_at
        ).total_seconds()
        job_history.error_message = str(e)
        logger.error(f"Job {job_id} failed: {e}", exc_info=True)

    session.add(job_history)
    session.commit()

    return {
        "status": "completed",
        "job_id": job_id,
        "job_name": job_name,
        "execution_id": job_history.id,
        "result": {
            "status": job_history.status,
            "duration_seconds": job_history.duration_seconds,
            "items_processed": job_history.items_processed,
            "error_message": job_history.error_message
        }
    }


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/users")
def get_users(
    page: int = 1,
    page_size: int = 50,
    search: Optional[str] = None,
    is_admin: Optional[bool] = None,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get paginated list of users with optional filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page (max 100)
        search: Search by email or name
        is_admin: Filter by admin status

    Returns:
        Paginated user list with total count
    """
    page_size = min(page_size, 100)  # Cap at 100
    offset = (page - 1) * page_size

    query = select(User)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (User.email.ilike(search_pattern)) |
            (User.name.ilike(search_pattern))
        )

    if is_admin is not None:
        query = query.where(User.is_admin == is_admin)

    # Get total count
    count_query = select(func.count(User.id))
    if search:
        search_pattern = f"%{search}%"
        count_query = count_query.where(
            (User.email.ilike(search_pattern)) |
            (User.name.ilike(search_pattern))
        )
    if is_admin is not None:
        count_query = count_query.where(User.is_admin == is_admin)

    total_count = session.exec(count_query).first()

    # Get paginated results
    users = session.exec(
        query.order_by(User.created_at.desc()).limit(page_size).offset(offset)
    ).all()

    return {
        "users": [
            {
                "id": user.id,
                "email": user.email,
                "name": user.name,
                "is_admin": user.is_admin,
                "is_active": user.is_active,
                "email_verified": user.email_verified,
                "subscription_tier": user.subscription_tier,
                "created_at": user.created_at.isoformat(),
                "last_login": user.last_login.isoformat() if user.last_login else None,
                "admin_notes": user.admin_notes
            }
            for user in users
        ],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.put("/users/{user_id}/admin")
def update_user_admin_status(
    user_id: int,
    is_admin: bool,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Grant or revoke admin privileges for a user.

    Args:
        user_id: ID of user to modify
        is_admin: True to grant admin, False to revoke

    Returns:
        Updated user info
    """
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    old_value = user.is_admin
    user.is_admin = is_admin
    session.add(user)
    session.commit()

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="update_user_admin",
        resource_type="user",
        resource_id=str(user_id),
        old_value=str(old_value),
        new_value=str(is_admin),
        session=session,
        request=request
    )

    logger.info(
        f"Admin {admin_user.email} {'granted' if is_admin else 'revoked'} "
        f"admin privileges for user {user.email}"
    )

    return {
        "id": user.id,
        "email": user.email,
        "is_admin": user.is_admin,
        "message": f"Admin status {'granted' if is_admin else 'revoked'}"
    }


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Delete a user (soft delete - sets is_active = False).

    Args:
        user_id: ID of user to delete

    Returns:
        Success message
    """
    if user_id == admin_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )

    user = session.get(User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    session.add(user)
    session.commit()

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="delete_user",
        resource_type="user",
        resource_id=str(user_id),
        old_value=user.email,
        session=session,
        request=request
    )

    logger.info(f"Admin {admin_user.email} deleted user {user.email}")

    return {
        "success": True,
        "message": f"User {user.email} deleted (soft delete)",
        "user_id": user_id
    }


# ============================================================================
# AUDIT LOG ENDPOINT
# ============================================================================

@router.get("/audit")
def get_audit_log(
    page: int = 1,
    page_size: int = 50,
    action_type: Optional[str] = None,
    user_id: Optional[int] = None,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get admin action audit log with optional filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page (max 100)
        action_type: Filter by action type
        user_id: Filter by admin user ID

    Returns:
        Paginated audit log entries
    """
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    query = select(AdminAuditLog)

    if action_type:
        query = query.where(AdminAuditLog.action_type == action_type)
    if user_id:
        query = query.where(AdminAuditLog.user_id == user_id)

    # Get total count
    count_query = select(func.count(AdminAuditLog.id))
    if action_type:
        count_query = count_query.where(AdminAuditLog.action_type == action_type)
    if user_id:
        count_query = count_query.where(AdminAuditLog.user_id == user_id)

    total_count = session.exec(count_query).first()

    # Get paginated results
    logs = session.exec(
        query.order_by(AdminAuditLog.timestamp.desc()).limit(page_size).offset(offset)
    ).all()

    return {
        "audit_logs": [
            {
                "id": log.id,
                "admin_email": log.admin_email,
                "action_type": log.action_type,
                "resource_type": log.resource_type,
                "resource_id": log.resource_id,
                "old_value": log.old_value,
                "new_value": log.new_value,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat(),
                "notes": log.notes
            }
            for log in logs
        ],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


# ============================================================================
# SOURCE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/sources")
def get_sources_admin(
    page: int = 1,
    page_size: int = 50,
    active_only: bool = False,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get paginated list of sources with article counts.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page (max 100)
        active_only: Only show active sources

    Returns:
        Paginated source list with stats
    """
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    query = select(Source)
    if active_only:
        query = query.where(Source.is_active == True)

    # Get total count
    count_query = select(func.count(Source.id))
    if active_only:
        count_query = count_query.where(Source.is_active == True)
    total_count = session.exec(count_query).first()

    # Get paginated results
    sources = session.exec(
        query.order_by(Source.created_at.desc()).limit(page_size).offset(offset)
    ).all()

    # Get article counts for each source
    sources_data = []
    for source in sources:
        article_count = session.exec(
            select(func.count(Article.id)).where(Article.source_id == source.id)
        ).first()

        sources_data.append({
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "rss_feed_url": source.rss_feed_url,
            "description": source.description,
            "trust_score": source.trust_score,
            "organizational_bias": source.organizational_bias,
            "is_active": source.is_active,
            "created_at": source.created_at.isoformat(),
            "article_count": article_count
        })

    return {
        "sources": sources_data,
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.put("/sources/{source_id}")
def update_source(
    source_id: int,
    is_active: Optional[bool] = None,
    trust_score: Optional[float] = None,
    request: Request = None,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Update source properties (activate/deactivate, adjust trust score).

    Args:
        source_id: ID of source to update
        is_active: Set active status
        trust_score: Update trust score (0.0-1.0)

    Returns:
        Updated source info
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )

    old_values = {
        "is_active": source.is_active,
        "trust_score": source.trust_score
    }

    if is_active is not None:
        source.is_active = is_active
    if trust_score is not None:
        if trust_score < 0.0 or trust_score > 1.0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="trust_score must be between 0.0 and 1.0"
            )
        source.trust_score = trust_score

    session.add(source)
    session.commit()

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="update_source",
        resource_type="source",
        resource_id=str(source_id),
        old_value=str(old_values),
        new_value=str({"is_active": source.is_active, "trust_score": source.trust_score}),
        session=session,
        request=request
    )

    logger.info(f"Admin {admin_user.email} updated source {source.name}")

    return {
        "id": source.id,
        "name": source.name,
        "is_active": source.is_active,
        "trust_score": source.trust_score,
        "message": "Source updated successfully"
    }


@router.delete("/sources/{source_id}")
def delete_source(
    source_id: int,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Delete a source (soft delete - sets is_active = False).

    Args:
        source_id: ID of source to delete

    Returns:
        Success message
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source not found"
        )

    source.is_active = False
    session.add(source)
    session.commit()

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="delete_source",
        resource_type="source",
        resource_id=str(source_id),
        old_value=source.name,
        session=session,
        request=request
    )

    logger.info(f"Admin {admin_user.email} deleted source {source.name}")

    return {
        "success": True,
        "message": f"Source {source.name} deleted (soft delete)",
        "source_id": source_id
    }


# ============================================================================
# ARTICLE MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/articles")
def get_articles_admin(
    page: int = 1,
    page_size: int = 50,
    source_id: Optional[int] = None,
    status: Optional[ProcessingStatus] = None,
    search: Optional[str] = None,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get paginated list of articles with filtering.

    Args:
        page: Page number (1-indexed)
        page_size: Results per page (max 100)
        source_id: Filter by source
        status: Filter by processing status
        search: Search in title

    Returns:
        Paginated article list
    """
    page_size = min(page_size, 100)
    offset = (page - 1) * page_size

    query = select(Article)

    if source_id:
        query = query.where(Article.source_id == source_id)
    if status:
        query = query.where(Article.processing_status == status)
    if search:
        query = query.where(Article.title.ilike(f"%{search}%"))

    # Get total count
    count_query = select(func.count(Article.id))
    if source_id:
        count_query = count_query.where(Article.source_id == source_id)
    if status:
        count_query = count_query.where(Article.processing_status == status)
    if search:
        count_query = count_query.where(Article.title.ilike(f"%{search}%"))

    total_count = session.exec(count_query).first()

    # Get paginated results
    articles = session.exec(
        query.order_by(Article.scraped_at.desc()).limit(page_size).offset(offset)
    ).all()

    return {
        "articles": [
            {
                "id": article.id,
                "title": article.title,
                "url": article.url,
                "source_id": article.source_id,
                "published_at": article.published_at.isoformat(),
                "scraped_at": article.scraped_at.isoformat(),
                "processing_status": article.processing_status,
                "word_count": article.word_count,
                "topic_category": article.topic_category
            }
            for article in articles
        ],
        "total_count": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": (total_count + page_size - 1) // page_size
    }


@router.delete("/articles/{article_id}")
def delete_article(
    article_id: int,
    request: Request,
    admin_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
) -> Dict[str, Any]:
    """
    Delete an article and all related data.

    Args:
        article_id: ID of article to delete

    Returns:
        Success message
    """
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )

    article_title = article.title

    # Delete article (cascade will handle related data)
    session.delete(article)
    session.commit()

    # Log admin action
    log_admin_action(
        admin_user=admin_user,
        action_type="delete_article",
        resource_type="article",
        resource_id=str(article_id),
        old_value=article_title,
        session=session,
        request=request
    )

    logger.info(f"Admin {admin_user.email} deleted article {article_id}: {article_title}")

    return {
        "success": True,
        "message": f"Article deleted: {article_title}",
        "article_id": article_id
    }
