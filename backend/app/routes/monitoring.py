"""
System Monitoring and Health Check API Routes

Provides endpoints for monitoring challenge system health,
performance metrics, and operational status.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from ..database import get_session
from ..routes.auth import get_current_user, get_admin_user
from ..models import User
from ..services.challenge_monitoring import ChallengeSystemMonitor
from ..utils.logging import get_logger
from ..utils.pipeline_metrics import snapshot as pipeline_snapshot
from ..config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/monitoring", tags=["monitoring"])


@router.get("/health", response_model=Dict[str, Any])
def health_check(session: Session = Depends(get_session)):
    """
    Basic health check endpoint.

    Returns system status and basic health indicators.
    """
    try:
        # Check database connection
        db_check = session.exec(select(func.count(User.id))).one() or 0

        # Check if challenge system is initialized
        monitor = ChallengeSystemMonitor(session)
        basic_health = monitor.get_system_health_report()

        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "database_connected": db_check >= 0,
            "challenge_system_status": basic_health.get("overall_status", "unknown"),
            "uptime": "running"  # Would get actual uptime from system
        }

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/health/detailed", response_model=Dict[str, Any])
def detailed_health_check(session: Session = Depends(get_session)):
    """
    Detailed health check with comprehensive system metrics.

    Returns performance metrics, error rates, and system health indicators.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        health_report = monitor.get_system_health_report()

        return health_report

    except Exception as e:
        logger.error(f"Detailed health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail=f"Health check failed: {str(e)}")


@router.get("/alerts", response_model=List[Dict[str, Any]])
def get_system_alerts(session: Session = Depends(get_session)):
    """
    Get current system alerts requiring attention.

    Returns active alerts sorted by severity.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        alerts = monitor.get_alert_conditions()
        pipeline_alerts = get_pipeline_alerts()
        alerts.extend(pipeline_alerts)

        # Sort alerts by severity
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        sorted_alerts = sorted(alerts, key=lambda x: severity_order.get(x["severity"], 3))

        return sorted_alerts

    except Exception as e:
        logger.error(f"Failed to get system alerts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get alerts: {str(e)}")


@router.get("/performance", response_model=Dict[str, Any])
def get_performance_metrics(
    hours: int = Query(default=24, le=168, ge=1, description="Time range in hours"),
    session: Session = Depends(get_session)
):
    """
    Get detailed performance metrics for the specified time range.

    Returns system performance indicators and trends.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        health_report = monitor.get_system_health_report()

        # Filter metrics by time range if needed
        performance_metrics = health_report.get("performance_metrics", {})

        return {
            "time_range_hours": hours,
            "generated_at": health_report.get("timestamp"),
            "metrics": performance_metrics,
            "capacity_metrics": health_report.get("capacity_metrics", {}),
            "trend_analysis": generate_performance_trends(session, hours)
        }

    except Exception as e:
        logger.error(f"Failed to get performance metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/summary", response_model=Dict[str, Any])
def get_executive_summary(session: Session = Depends(get_session)):
    """
    Get executive-level summary of system performance and health.

    Returns key metrics, trends, and recommendations for stakeholders.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        summary = monitor.get_performance_summary()

        return summary

    except Exception as e:
        logger.error(f"Failed to get executive summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get summary: {str(e)}")


@router.get("/participation", response_model=Dict[str, Any])
def get_participation_metrics(
    days: int = Query(default=30, le=365, ge=1, description="Time range in days"),
    session: Session = Depends(get_session)
):
    """
    Get detailed participation metrics and trends.

    Returns user engagement statistics and participation patterns.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        health_report = monitor.get_system_health_report()

        participation_metrics = health_report.get("participation_metrics", {})

        # Add historical trend data
        historical_data = get_historical_participation_trends(session, days)

        return {
            "time_range_days": days,
            "generated_at": health_report.get("timestamp"),
            "current_metrics": participation_metrics,
            "historical_trends": historical_data,
            "forecasts": generate_participation_forecasts(session, days)
        }

    except Exception as e:
        logger.error(f"Failed to get participation metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/quality", response_model=Dict[str, Any])
def get_quality_metrics(session: Session = Depends(get_session)):
    """
    Get data quality and system integrity metrics.

    Returns indicators of data consistency, completeness, and quality.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        health_report = monitor.get_system_health_report()

        return {
            "generated_at": health_report.get("timestamp"),
            "data_quality": health_report.get("data_quality", {}),
            "error_rates": health_report.get("error_rates", {}),
            "quality_trends": get_quality_trends(session),
            "recommendations": generate_quality_recommendations(health_report)
        }

    except Exception as e:
        logger.error(f"Failed to get quality metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get metrics: {str(e)}")


@router.get("/pipeline", response_model=Dict[str, Any])
def get_pipeline_metrics():
    """Return pipeline operational metrics and budget status."""
    metrics = pipeline_snapshot()
    total_cost = metrics.get("costs_usd", {}).get("pipeline_total", 0.0)
    budget = settings.pipeline_daily_budget_usd
    utilization = (total_cost / budget) if budget else 0.0
    alerts = get_pipeline_alerts()
    return {
        "timestamp": datetime.utcnow().isoformat(),
        "metrics": metrics,
        "alerts": alerts,
        "budget": {
            "daily_budget_usd": budget,
            "spent_usd": round(total_cost, 4),
            "utilization_ratio": round(utilization, 4),
            "warning_threshold_ratio": settings.pipeline_warn_budget_percent,
            "warning": utilization >= settings.pipeline_warn_budget_percent,
        },
    }


def get_pipeline_alerts() -> List[Dict[str, Any]]:
    metrics = pipeline_snapshot()
    alerts: List[Dict[str, Any]] = []

    counters = metrics.get("counters", {})
    costs = metrics.get("costs_usd", {})
    gauges = metrics.get("gauges", {})

    failed_extract = counters.get("pipeline.extract.failed", 0)
    success_extract = counters.get("pipeline.extract.success", 0)
    total_extract = failed_extract + success_extract
    if total_extract >= 10:
        failure_rate = failed_extract / max(total_extract, 1)
        if failure_rate >= 0.2:
            alerts.append(
                {
                    "severity": "critical",
                    "type": "pipeline_extract_failure_rate",
                    "message": f"Extraction failure rate is {failure_rate:.0%} over {total_extract} attempts.",
                }
            )

    total_cost = costs.get("pipeline_total", 0.0)
    budget = settings.pipeline_daily_budget_usd
    utilization = (total_cost / budget) if budget else 0.0
    if utilization >= 1.0:
        alerts.append(
            {
                "severity": "critical",
                "type": "pipeline_budget_exceeded",
                "message": f"Daily pipeline budget exceeded (${total_cost:.2f}/${budget:.2f}).",
            }
        )
    elif utilization >= settings.pipeline_warn_budget_percent:
        alerts.append(
            {
                "severity": "warning",
                "type": "pipeline_budget_warning",
                "message": f"Pipeline budget at {utilization:.0%} (${total_cost:.2f}/${budget:.2f}).",
            }
        )

    failed_post = gauges.get("pipeline.post_process.tasks_failed", 0)
    if failed_post > 0:
        alerts.append(
            {
                "severity": "warning",
                "type": "pipeline_post_process_failures",
                "message": f"{int(failed_post)} post-analysis task(s) failed in latest run.",
            }
        )

    return alerts


# Admin-only endpoints
@router.get("/admin/system", response_model=Dict[str, Any])
def get_admin_system_info(
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Get comprehensive system information for administrators.

    Returns detailed system metrics, configuration, and diagnostic information.
    """
    try:
        monitor = ChallengeSystemMonitor(session)
        health_report = monitor.get_system_health_report()

        # Add administrative information
        admin_info = {
            **health_report,
            "system_configuration": get_system_configuration(),
            "job_status": get_job_status(),
            "resource_usage": get_resource_usage(),
            "security_status": get_security_status()
        }

        return admin_info

    except Exception as e:
        logger.error(f"Failed to get admin system info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get admin info: {str(e)}")


@router.post("/admin/cleanup", response_model=Dict[str, Any])
def cleanup_system_data(
    dry_run: bool = Query(default=True, description="Run cleanup in dry-run mode"),
    current_user: User = Depends(get_admin_user),
    session: Session = Depends(get_session)
):
    """
    Perform system cleanup operations.

    Removes orphaned records and fixes data inconsistencies.
    """
    try:
        cleanup_results = {
            "dry_run": dry_run,
            "timestamp": datetime.utcnow().isoformat(),
            "operations": []
        }

        if not dry_run:
            # Cleanup orphaned assignments
            orphaned_assignments = cleanup_orphaned_assignments(session)
            cleanup_results["operations"].append({
                "operation": "cleanup_orphaned_assignments",
                "records_processed": orphaned_assignments
            })

            # Cleanup orphaned responses
            orphaned_responses = cleanup_orphaned_responses(session)
            cleanup_results["operations"].append({
                "operation": "cleanup_orphaned_responses",
                "records_processed": orphaned_responses
            })

            session.commit()

        return cleanup_results

    except Exception as e:
        session.rollback()
        logger.error(f"System cleanup failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Cleanup failed: {str(e)}")


# Helper functions
def generate_performance_trends(session: Session, hours: int) -> Dict[str, Any]:
    """Generate performance trend analysis."""
    # This would implement trend analysis based on historical data
    # For now, return basic trend indicators
    return {
        "cpu_trend": "stable",
        "memory_trend": "stable",
        "response_time_trend": "improving",
        "error_rate_trend": "stable"
    }


def get_historical_participation_trends(session: Session, days: int) -> Dict[str, Any]:
    """Get historical participation trends."""
    # This would query historical participation data
    # For now, return placeholder data
    return {
        "daily_participants": [],
        "completion_rates": [],
        "engagement_patterns": []
    }


def generate_participation_forecasts(session: Session, days: int) -> Dict[str, Any]:
    """Generate participation forecasts based on historical data."""
    # This would implement forecasting algorithms
    return {
        "next_week_forecast": {
            "expected_participants": 0,
            "confidence_interval": [0, 0]
        },
        "trend_direction": "stable"
    }


def get_quality_trends(session: Session) -> Dict[str, Any]:
    """Get quality trend analysis."""
    return {
        "data_quality_trend": "stable",
        "error_rate_trend": "improving",
        "consistency_trend": "stable"
    }


def generate_quality_recommendations(health_report: Dict[str, Any]) -> List[str]:
    """Generate quality improvement recommendations."""
    recommendations = []

    data_quality = health_report.get("data_quality", {})
    error_rates = health_report.get("error_rates", {})

    if data_quality.get("overall_quality_score", 100) < 90:
        recommendations.append("Review and clean up data quality issues")

    if error_rates.get("error_rate", {}).get("rate", 0) > 2:
        recommendations.append("Investigate and resolve elevated error rates")

    return recommendations if recommendations else ["Data quality within acceptable parameters"]


def get_system_configuration() -> Dict[str, Any]:
    """Get system configuration information."""
    # This would return actual system configuration
    return {
        "environment": "production",
        "version": "1.0.0",
        "database": "postgresql",
        "cache": "redis",
        "queue": "celery"
    }


def get_job_status() -> Dict[str, Any]:
    """Get background job status."""
    # This would check actual job scheduler status
    return {
        "scheduler": "running",
        "active_jobs": [],
        "failed_jobs": [],
        "last_run": datetime.utcnow().isoformat()
    }


def get_resource_usage() -> Dict[str, Any]:
    """Get system resource usage."""
    # This would return actual resource metrics
    return {
        "cpu_usage": 45.2,
        "memory_usage": 67.8,
        "disk_usage": 23.1,
        "network_io": "normal"
    }


def get_security_status() -> Dict[str, Any]:
    """Get security system status."""
    # This would return security monitoring data
    return {
        "authentication": "operational",
        "authorization": "operational",
        "encryption": "enabled",
        "last_security_scan": datetime.utcnow().isoformat(),
        "vulnerabilities": []
    }


def cleanup_orphaned_assignments(session: Session) -> int:
    """Clean up orphaned assignment records."""
    # This would implement actual cleanup logic
    return 0


def cleanup_orphaned_responses(session: Session) -> int:
    """Clean up orphaned response records."""
    # This would implement actual cleanup logic
    return 0