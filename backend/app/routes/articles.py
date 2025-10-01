"""
Public routes for viewing articles and their analysis.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.database import get_session
from app.models import Article, ArticleAnalysis, Source
from typing import List, Optional

router = APIRouter(prefix="/articles", tags=["articles"])


@router.get("/analyzed")
def get_analyzed_articles(
    limit: int = 10,
    offset: int = 0,
    session: Session = Depends(get_session)
):
    """
    Get articles that have been analyzed with AI summaries.

    Returns article with full analysis including:
    - Summary (100 words)
    - Sentiment score
    - Political lean
    - Bias indicators
    - Key statistics
    """
    # Get analyzed articles with their analysis
    query = (
        select(Article, ArticleAnalysis, Source)
        .join(ArticleAnalysis, Article.id == ArticleAnalysis.article_id)
        .join(Source, Article.source_id == Source.id)
        .order_by(Article.scraped_at.desc())
        .offset(offset)
        .limit(limit)
    )

    results = session.exec(query).all()

    articles_data = []
    for article, analysis, source in results:
        articles_data.append({
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "source": {
                "name": source.name,
                "url": source.url
            },
            "published_at": article.published_at.isoformat() if article.published_at else None,
            "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None,
            "word_count": article.word_count,
            "analysis": {
                "summary": analysis.summary,
                "sentiment_score": analysis.sentiment_score,
                "political_lean": analysis.political_lean.value if analysis.political_lean else None,
                "bias_indicators": analysis.bias_indicators,
                "key_stats": analysis.key_stats,
                "processed_at": analysis.processed_at.isoformat() if analysis.processed_at else None
            }
        })

    return {
        "total": len(articles_data),
        "articles": articles_data
    }


@router.get("/{article_id}")
def get_article_detail(
    article_id: int,
    session: Session = Depends(get_session)
):
    """
    Get detailed information about a specific article including full content and analysis.
    """
    article = session.get(Article, article_id)
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")

    # Get source
    source = session.get(Source, article.source_id)

    # Get analysis if it exists
    analysis = session.exec(
        select(ArticleAnalysis)
        .where(ArticleAnalysis.article_id == article_id)
    ).first()

    response = {
        "id": article.id,
        "title": article.title,
        "url": article.url,
        "source": {
            "name": source.name,
            "url": source.url
        } if source else None,
        "published_at": article.published_at.isoformat() if article.published_at else None,
        "scraped_at": article.scraped_at.isoformat() if article.scraped_at else None,
        "word_count": article.word_count,
        "processing_status": article.processing_status.value,
        "content_preview": article.content_text[:500] if article.content_text else None,
        "has_full_content": bool(article.content_text),
        "analysis": None
    }

    if analysis:
        response["analysis"] = {
            "summary": analysis.summary,
            "sentiment_score": analysis.sentiment_score,
            "political_lean": analysis.political_lean.value if analysis.political_lean else None,
            "bias_indicators": analysis.bias_indicators,
            "key_stats": analysis.key_stats,
            "processed_at": analysis.processed_at.isoformat() if analysis.processed_at else None
        }

    return response
