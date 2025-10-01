"""
Admin routes for monitoring and manual job triggers.
"""

from fastapi import APIRouter, Depends, BackgroundTasks
from sqlmodel import Session, select, func
from app.models import Article, Source, Framework, User, ProcessingStatus
from app.database import get_session
from app.jobs.tasks import scrape_job, extract_job, analyze_job, framework_job
from app.jobs.scheduler import get_job_status
from datetime import datetime, timedelta
from typing import Dict, Any

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
def get_system_stats(session: Session = Depends(get_session)) -> Dict[str, Any]:
    """
    Get comprehensive system statistics.
    """
    # Article counts by status
    total_articles = session.exec(select(func.count(Article.id))).first()

    pending_count = session.exec(
        select(func.count(Article.id))
        .where(Article.processing_status == ProcessingStatus.PENDING)
    ).first()

    completed_count = session.exec(
        select(func.count(Article.id))
        .where(Article.processing_status == ProcessingStatus.COMPLETED)
    ).first()

    failed_count = session.exec(
        select(func.count(Article.id))
        .where(Article.processing_status == ProcessingStatus.FAILED)
    ).first()

    # Average word count
    avg_word_count = session.exec(
        select(func.avg(Article.word_count))
        .where(Article.word_count.isnot(None))
    ).first()

    # Recent articles (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_articles = session.exec(
        select(func.count(Article.id))
        .where(Article.scraped_at >= yesterday)
    ).first()

    # Source counts
    total_sources = session.exec(select(func.count(Source.id))).first()
    active_sources = session.exec(
        select(func.count(Source.id))
        .where(Source.is_active == True)
    ).first()

    # Framework counts
    total_frameworks = session.exec(select(func.count(Framework.id))).first()
    seed_frameworks = session.exec(
        select(func.count(Framework.id))
        .where(Framework.is_seed == True)
    ).first()

    # User count
    total_users = session.exec(select(func.count(User.id))).first()

    # Extraction success rate
    success_rate = 0
    if total_articles and total_articles > 0:
        success_rate = (completed_count / total_articles) * 100 if completed_count else 0

    return {
        "articles": {
            "total": total_articles,
            "pending": pending_count,
            "completed": completed_count,
            "failed": failed_count,
            "recent_24h": recent_articles,
            "avg_word_count": int(avg_word_count) if avg_word_count else 0,
            "extraction_success_rate": round(success_rate, 2)
        },
        "sources": {
            "total": total_sources,
            "active": active_sources
        },
        "frameworks": {
            "total": total_frameworks,
            "seed": seed_frameworks,
            "ai_generated": total_frameworks - seed_frameworks if total_frameworks else 0
        },
        "users": {
            "total": total_users
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/scheduler/status")
def get_scheduler_status() -> Dict[str, Any]:
    """
    Get status of all scheduled jobs.
    """
    return get_job_status()


@router.post("/jobs/scrape")
def trigger_scrape_job(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Manually trigger RSS scraping job in the background.
    """
    background_tasks.add_task(scrape_job)
    return {
        "status": "triggered",
        "job": "scrape_rss",
        "message": "RSS scraping job started in background"
    }


@router.post("/jobs/extract")
def trigger_extract_job(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Manually trigger article extraction job in the background.
    """
    background_tasks.add_task(extract_job)
    return {
        "status": "triggered",
        "job": "extract_articles",
        "message": "Article extraction job started in background"
    }


@router.post("/jobs/analyze")
def trigger_analyze_job(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Manually trigger AI analysis job in the background.
    """
    background_tasks.add_task(analyze_job)
    return {
        "status": "triggered",
        "job": "analyze_articles",
        "message": "AI analysis job started in background"
    }


@router.post("/jobs/frameworks")
def trigger_framework_job(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Manually trigger framework update job in the background.
    """
    background_tasks.add_task(framework_job)
    return {
        "status": "triggered",
        "job": "update_frameworks",
        "message": "Framework update job started in background"
    }


@router.get("/articles/recent")
def get_recent_articles(
    limit: int = 10,
    session: Session = Depends(get_session)
):
    """
    Get most recently scraped articles with basic info.
    """
    articles = session.exec(
        select(Article)
        .order_by(Article.scraped_at.desc())
        .limit(limit)
    ).all()

    return [
        {
            "id": article.id,
            "title": article.title,
            "source_id": article.source_id,
            "url": article.url,
            "published_at": article.published_at.isoformat(),
            "scraped_at": article.scraped_at.isoformat(),
            "status": article.processing_status,
            "word_count": article.word_count,
            "extraction_method": article.extraction_method
        }
        for article in articles
    ]


@router.get("/sources/status")
def get_sources_status(session: Session = Depends(get_session)):
    """
    Get article counts per source.
    """
    sources = session.exec(select(Source)).all()

    source_stats = []
    for source in sources:
        article_count = session.exec(
            select(func.count(Article.id))
            .where(Article.source_id == source.id)
        ).first()

        completed_count = session.exec(
            select(func.count(Article.id))
            .where(Article.source_id == source.id)
            .where(Article.processing_status == ProcessingStatus.COMPLETED)
        ).first()

        source_stats.append({
            "id": source.id,
            "name": source.name,
            "is_active": source.is_active,
            "article_count": article_count,
            "completed_count": completed_count,
            "trust_score": source.trust_score
        })

    return source_stats
