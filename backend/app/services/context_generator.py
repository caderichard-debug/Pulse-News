"""
Context Generation Service

Generates comprehensive background context for news articles using AI.
"""

import json
import logging
from typing import Optional, Dict, List
from datetime import datetime
from sqlmodel import Session, select
from app.models import Article, ArticleAnalysis, ArticleContext
from app.config import settings
import openai

logger = logging.getLogger(__name__)


CONTEXT_GENERATION_PROMPT = """Generate comprehensive background context for this news article to help readers understand the bigger picture.

Article Title: {title}
Article Summary: {summary}
Publication Date: {published_at}

Provide the following in JSON format:

{{
  "background": "3-4 sentences explaining what led to this story. Include relevant history and context.",
  "key_players": ["List", "of", "main", "people", "or", "organizations", "involved"],
  "timeline": [
    {{"date": "YYYY-MM", "event": "Brief description of key event"}},
    {{"date": "YYYY-MM", "event": "Another key event"}}
  ],
  "significance": "2-3 sentences explaining why this matters and what the broader implications are.",
  "next_developments": "1-2 sentences on what to expect next or what to watch for.",
  "quality_score": 0.0-1.0 (your confidence in the context quality)
}}

Guidelines:
- Be concise but informative
- Focus on facts, not opinions
- Include 4-7 timeline events
- Quality score should reflect completeness and accuracy
- If information is uncertain, acknowledge it

Return only the JSON object, no other text.
"""


def generate_article_context(
    article: Article,
    analysis: ArticleAnalysis,
    session: Session
) -> Optional[ArticleContext]:
    """
    Generate comprehensive context for an article using AI.

    Args:
        article: The article to generate context for
        analysis: The article's analysis
        session: Database session

    Returns:
        ArticleContext object or None if generation fails
    """
    if not settings.openai_api_key:
        logger.warning("OpenAI API key not configured, skipping context generation")
        return None

    # Check if context already exists
    existing = session.exec(
        select(ArticleContext)
        .where(ArticleContext.article_id == article.id)
    ).first()

    if existing:
        logger.debug(f"Context already exists for article {article.id}")
        return existing

    try:
        # Prepare prompt
        prompt = CONTEXT_GENERATION_PROMPT.format(
            title=article.title,
            summary=analysis.summary,
            published_at=article.published_at.strftime("%B %d, %Y")
        )

        # Call OpenAI
        openai.api_key = settings.openai_api_key
        response = openai.ChatCompletion.create(
            model=settings.ai_model,
            messages=[
                {
                    "role": "system",
                    "content": "You are a knowledgeable news analyst who provides clear, factual context for current events."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            max_tokens=1000
        )

        # Parse response
        content = response.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        context_data = json.loads(content)

        # Create ArticleContext object
        context = ArticleContext(
            article_id=article.id,
            background=context_data.get("background"),
            key_players=json.dumps(context_data.get("key_players", [])),
            timeline=json.dumps(context_data.get("timeline", [])),
            significance=context_data.get("significance"),
            next_developments=context_data.get("next_developments"),
            context_quality_score=context_data.get("quality_score", 0.7),
            tokens_used=response.usage.total_tokens if hasattr(response, 'usage') else None
        )

        session.add(context)

        # Update analysis to mark that context exists
        analysis.has_context = True
        session.add(analysis)
        session.commit()

        logger.info(f"Generated context for article {article.id}")
        return context

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse context generation response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"Error generating context: {e}", exc_info=True)
        return None


def process_article_contexts(session: Session, limit: int = 5) -> Dict[str, int]:
    """
    Generate context for articles that don't have it yet.

    Args:
        session: Database session
        limit: Maximum number of articles to process

    Returns:
        Dict with statistics
    """
    stats = {
        "articles_processed": 0,
        "contexts_generated": 0,
        "total_tokens": 0
    }

    # Find analyzed articles without context
    articles = session.exec(
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(ArticleAnalysis.has_context == False)
        .order_by(Article.published_at.desc())
        .limit(limit)
    ).all()

    logger.info(f"Processing context for {len(articles)} articles")

    for article, analysis in articles:
        try:
            context = generate_article_context(article, analysis, session)
            stats["articles_processed"] += 1

            if context:
                stats["contexts_generated"] += 1
                if context.tokens_used:
                    stats["total_tokens"] += context.tokens_used

                session.commit()
            else:
                session.rollback()

        except Exception as e:
            logger.error(f"Error processing context for article {article.id}: {e}", exc_info=True)
            session.rollback()
            continue

    logger.info(
        f"Context generation complete: {stats['articles_processed']} processed, "
        f"{stats['contexts_generated']} generated, {stats['total_tokens']} tokens used"
    )

    return stats


def get_article_context(article_id: int, session: Session) -> Optional[Dict]:
    """
    Get context for an article in a structured format.

    Args:
        article_id: The article ID
        session: Database session

    Returns:
        Dict with context data or None
    """
    context = session.exec(
        select(ArticleContext)
        .where(ArticleContext.article_id == article_id)
    ).first()

    if not context:
        return None

    # Parse JSON fields
    key_players = json.loads(context.key_players) if context.key_players else []
    timeline = json.loads(context.timeline) if context.timeline else []

    return {
        "background": context.background,
        "key_players": key_players,
        "timeline": timeline,
        "significance": context.significance,
        "next_developments": context.next_developments,
        "quality_score": context.context_quality_score,
        "generated_at": context.generated_at.isoformat()
    }


def format_context_for_newsletter(context: ArticleContext) -> str:
    """
    Format context data as HTML for newsletter display.

    Args:
        context: The ArticleContext object

    Returns:
        HTML string
    """
    if not context:
        return ""

    html_parts = []

    # Background
    if context.background:
        html_parts.append(f"""
        <div style="margin-bottom: 15px;">
            <strong style="color: #1976D2;">📖 Background</strong><br>
            <span style="font-size: 13px; color: #555;">{context.background}</span>
        </div>
        """)

    # Key Players
    if context.key_players:
        try:
            players = json.loads(context.key_players)
            if players:
                players_html = "<br>".join([f"• {player}" for player in players])
                html_parts.append(f"""
                <div style="margin-bottom: 15px;">
                    <strong style="color: #1976D2;">👥 Key Players</strong><br>
                    <span style="font-size: 13px; color: #555;">{players_html}</span>
                </div>
                """)
        except:
            pass

    # Timeline
    if context.timeline:
        try:
            timeline = json.loads(context.timeline)
            if timeline:
                timeline_html = "<br>".join([
                    f"• <strong>{event.get('date', 'N/A')}</strong>: {event.get('event', '')}"
                    for event in timeline
                ])
                html_parts.append(f"""
                <div style="margin-bottom: 15px;">
                    <strong style="color: #1976D2;">⏱️ Timeline</strong><br>
                    <span style="font-size: 13px; color: #555;">{timeline_html}</span>
                </div>
                """)
        except:
            pass

    # Significance
    if context.significance:
        html_parts.append(f"""
        <div style="margin-bottom: 15px;">
            <strong style="color: #1976D2;">💡 Why This Matters</strong><br>
            <span style="font-size: 13px; color: #555;">{context.significance}</span>
        </div>
        """)

    # Next Developments
    if context.next_developments:
        html_parts.append(f"""
        <div style="margin-bottom: 10px;">
            <strong style="color: #1976D2;">🔮 What's Next</strong><br>
            <span style="font-size: 13px; color: #555;">{context.next_developments}</span>
        </div>
        """)

    return "\n".join(html_parts)
