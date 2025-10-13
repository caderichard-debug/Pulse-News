"""
Sources API Routes

Endpoints for managing news sources and viewing source information.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func, col
from typing import List, Optional
from datetime import datetime

from app.database import get_session
from app.models import Source, Article, OrganizationalBias
from app.routes.auth import get_current_user
from app.services.bias_data_fetcher import get_bias_for_source

router = APIRouter(prefix="/sources", tags=["sources"])


# Response models
class SourceResponse:
    """Response model for source information."""
    def __init__(self, source: Source, article_count: int = 0):
        self.id = source.id
        self.name = source.name
        self.url = source.url
        self.rss_feed_url = source.rss_feed_url
        self.description = source.description
        self.trust_score = source.trust_score
        self.organizational_bias = source.organizational_bias.value if source.organizational_bias else None
        self.bias_description = source.bias_description
        self.is_active = source.is_active
        self.created_at = source.created_at.isoformat()
        self.article_count = article_count


class CreateSourceRequest:
    """Request model for creating a new source."""
    pass  # Will use dict validation


@router.get("")
async def list_sources(
    bias: Optional[str] = Query(None, description="Filter by organizational bias"),
    active_only: bool = Query(True, description="Show only active sources"),
    sort_by: str = Query("name", description="Sort by: name, trust_score, article_count"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    List all news sources with optional filtering and sorting.

    Returns source information including bias ratings and article counts.
    """
    # Build base query
    query = select(Source)

    # Apply filters
    if active_only:
        query = query.where(Source.is_active == True)

    if bias:
        try:
            bias_enum = OrganizationalBias(bias)
            query = query.where(Source.organizational_bias == bias_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid bias value: {bias}")

    # Get sources
    sources = session.exec(query).all()

    # Get article counts
    article_count_query = (
        select(Article.source_id, func.count(Article.id).label("count"))
        .group_by(Article.source_id)
    )
    article_counts = {row[0]: row[1] for row in session.exec(article_count_query)}

    # Build response with article counts
    source_responses = [
        SourceResponse(source, article_counts.get(source.id, 0)).__dict__
        for source in sources
    ]

    # Sort results
    if sort_by == "name":
        source_responses.sort(key=lambda x: x["name"])
    elif sort_by == "trust_score":
        source_responses.sort(key=lambda x: x["trust_score"], reverse=True)
    elif sort_by == "article_count":
        source_responses.sort(key=lambda x: x["article_count"], reverse=True)

    return {
        "sources": source_responses,
        "total_count": len(source_responses)
    }


@router.get("/{source_id}")
async def get_source(
    source_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Get detailed information about a specific source.
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Get article count
    article_count = session.exec(
        select(func.count(Article.id)).where(Article.source_id == source_id)
    ).one()

    return SourceResponse(source, article_count).__dict__


@router.post("")
async def create_source(
    name: str,
    url: str,
    rss_feed_url: str,
    description: Optional[str] = None,
    trust_score: float = 0.8,
    fetch_bias: bool = Query(True, description="Automatically fetch bias data"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Create a new news source.

    If fetch_bias=True, will attempt to automatically fetch organizational bias
    from external APIs/databases. Otherwise, bias can be set manually later.

    Requires authentication.
    """
    # Validate trust score
    if not (0.0 <= trust_score <= 1.0):
        raise HTTPException(status_code=400, detail="trust_score must be between 0.0 and 1.0")

    # Check if RSS feed URL already exists
    existing = session.exec(
        select(Source).where(Source.rss_feed_url == rss_feed_url)
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Source with RSS feed URL '{rss_feed_url}' already exists"
        )

    # Fetch bias data if requested
    organizational_bias = None
    bias_description = None

    if fetch_bias:
        try:
            bias_enum, bias_desc = await get_bias_for_source(url)
            organizational_bias = bias_enum
            bias_description = bias_desc
        except Exception as e:
            # Log error but don't fail - bias can be added manually later
            print(f"Failed to fetch bias data: {e}")
            bias_description = "Bias rating pending research."

    # Create source
    source = Source(
        name=name,
        url=url,
        rss_feed_url=rss_feed_url,
        description=description,
        trust_score=trust_score,
        organizational_bias=organizational_bias,
        bias_description=bias_description,
        is_active=True,
        created_at=datetime.utcnow()
    )

    session.add(source)
    session.commit()
    session.refresh(source)

    return {
        "message": "Source created successfully",
        "source": SourceResponse(source, 0).__dict__,
        "bias_auto_fetched": fetch_bias and organizational_bias is not None
    }


@router.put("/{source_id}")
async def update_source(
    source_id: int,
    name: Optional[str] = None,
    url: Optional[str] = None,
    rss_feed_url: Optional[str] = None,
    description: Optional[str] = None,
    trust_score: Optional[float] = None,
    organizational_bias: Optional[str] = None,
    bias_description: Optional[str] = None,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Update an existing source.

    Only provided fields will be updated.
    Requires authentication.
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    # Update fields
    if name is not None:
        source.name = name
    if url is not None:
        source.url = url
    if rss_feed_url is not None:
        # Check for duplicates
        existing = session.exec(
            select(Source)
            .where(Source.rss_feed_url == rss_feed_url)
            .where(Source.id != source_id)
        ).first()
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Another source with RSS feed URL '{rss_feed_url}' already exists"
            )
        source.rss_feed_url = rss_feed_url
    if description is not None:
        source.description = description
    if trust_score is not None:
        if not (0.0 <= trust_score <= 1.0):
            raise HTTPException(status_code=400, detail="trust_score must be between 0.0 and 1.0")
        source.trust_score = trust_score
    if organizational_bias is not None:
        try:
            source.organizational_bias = OrganizationalBias(organizational_bias)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid bias value: {organizational_bias}")
    if bias_description is not None:
        source.bias_description = bias_description
    if is_active is not None:
        source.is_active = is_active

    session.commit()
    session.refresh(source)

    # Get article count
    article_count = session.exec(
        select(func.count(Article.id)).where(Article.source_id == source_id)
    ).one()

    return {
        "message": "Source updated successfully",
        "source": SourceResponse(source, article_count).__dict__
    }


@router.delete("/{source_id}")
async def delete_source(
    source_id: int,
    hard_delete: bool = Query(False, description="Permanently delete (vs soft delete)"),
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete a source.

    By default, performs soft delete (sets is_active=False).
    Use hard_delete=True to permanently remove (not recommended if articles exist).

    Requires authentication.
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    if hard_delete:
        # Check for associated articles
        article_count = session.exec(
            select(func.count(Article.id)).where(Article.source_id == source_id)
        ).one()

        if article_count > 0:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot hard delete source with {article_count} associated articles. Use soft delete instead."
            )

        session.delete(source)
        session.commit()
        return {"message": "Source permanently deleted"}
    else:
        # Soft delete
        source.is_active = False
        session.commit()
        return {"message": "Source deactivated (soft delete)"}


@router.post("/{source_id}/fetch-bias")
async def fetch_bias_for_source(
    source_id: int,
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)
):
    """
    Manually trigger bias data fetch for a source.

    Useful for updating bias information or fetching it for sources
    created without automatic bias fetching.
    """
    source = session.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")

    try:
        bias_enum, bias_desc = await get_bias_for_source(source.url)

        if bias_enum:
            source.organizational_bias = bias_enum
            source.bias_description = bias_desc
            session.commit()
            session.refresh(source)

            return {
                "message": "Bias data fetched and updated successfully",
                "source": SourceResponse(source, 0).__dict__
            }
        else:
            return {
                "message": "No bias data found for this source",
                "source": SourceResponse(source, 0).__dict__
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch bias data: {str(e)}")
