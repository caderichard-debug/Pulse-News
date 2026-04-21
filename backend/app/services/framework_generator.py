"""
Framework generation and article mapping service.
This is the "competitive edge" - mapping articles to underlying ethical debates.
"""

from sqlmodel import Session, select, func
from ..models import (
    Article, ArticleAnalysis, Framework, ArticleFrameworkLink
)
from ..database import engine
from ..utils.openai_client import openai_client
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
import json

logger = logging.getLogger(__name__)


def refresh_framework_article_counts(session: Session) -> None:
    """
    Recompute Framework.article_count from ArticleFrameworkLink rows.
    Call after mapping commits or as a maintenance reconcile.
    """
    frameworks = session.exec(select(Framework)).all()
    for fw in frameworks:
        cnt = session.exec(
            select(func.count())
            .select_from(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.framework_id == fw.id)
        ).one()
        fw.article_count = int(cnt or 0)
        session.add(fw)


def map_articles_to_frameworks(
    session: Session,
    article_ids: List[int] = None,
    limit: int = 10
) -> int:
    """
    Map analyzed articles to existing frameworks using AI.

    Args:
        session: Database session (injected for testing)
        article_ids: Specific article IDs to map, or None for recent unanalyzed ones
        limit: Maximum number of articles to process

    Returns:
        Number of article-framework mappings created
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    mappings_created = 0

    # Get frameworks to map against
    frameworks = session.exec(select(Framework)).all()

    if not frameworks:
        logger.warning("No frameworks available for mapping")
        return 0

    # Get articles to map
    if article_ids:
        articles = session.exec(
            select(Article)
            .where(Article.id.in_(article_ids))
        ).all()
    else:
        # Get recently analyzed articles that haven't been mapped yet
        articles = session.exec(
            select(Article)
            .join(ArticleAnalysis)
            .where(~Article.id.in_(
                select(ArticleFrameworkLink.article_id)
            ))
            .limit(limit)
        ).all()

    if not articles:
        logger.info("No articles to map")
        return 0

    logger.info(f"Mapping {len(articles)} articles to {len(frameworks)} frameworks...")

    # Build framework descriptions for the prompt
    framework_descriptions = {}
    for fw in frameworks:
        framework_descriptions[fw.id] = {
            "name": fw.name,
            "description": fw.description,
            "axis": f"{fw.left_position} ←→ {fw.right_position}"
        }

    # Process each article
    for article in articles:
        # Get the analysis
        analysis = session.exec(
            select(ArticleAnalysis)
            .where(ArticleAnalysis.article_id == article.id)
        ).first()

        if not analysis:
            logger.warning(f"No analysis found for article {article.id}")
            continue

        # Ask OpenAI to map this article to frameworks
        framework_list = [
            {
                "id": fw_id,
                "name": fw_info["name"],
                "description": fw_info["description"],
                "axis_description": fw_info["axis"],
                "left_position": "",
                "right_position": ""
            }
            for fw_id, fw_info in framework_descriptions.items()
        ]

        try:
            mappings = openai_client.map_article_to_frameworks(
                article.title,
                analysis.summary,
                framework_list
            )

            if not mappings:
                logger.warning(f"No mappings returned for article {article.id}")
                continue

            # Create framework links
            for mapping in mappings:
                framework_id = mapping.get('framework_id')
                if framework_id not in framework_descriptions:
                    logger.warning(f"Invalid framework_id {framework_id}")
                    continue

                link = ArticleFrameworkLink(
                    article_id=article.id,
                    framework_id=framework_id,
                    relevance_score=mapping.get('relevance_score', 0.5),
                    position_on_axis=mapping.get('position_on_axis', mapping.get('position', 0)),
                    ai_explanation=mapping.get('explanation', '')[:500],
                    created_at=datetime.utcnow()
                )

                session.add(link)
                mappings_created += 1

                logger.info(
                    f"  ✓ Mapped '{article.title[:40]}...' to framework '{framework_descriptions[framework_id]['name']}'"
                )

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse framework mapping response: {e}")
            continue
        except Exception as e:
            logger.error(f"Error mapping article {article.id}: {e}")
            continue

    session.flush()
    refresh_framework_article_counts(session)
    session.commit()
    logger.info(
        f"Created {mappings_created} framework mappings; refreshed framework article_count"
    )

    return mappings_created


def discover_new_frameworks(session: Session, min_articles: int = 50) -> int:
    """
    Use AI to discover new ethical frameworks from recent articles.
    This is run weekly to evolve the framework library.

    Args:
        session: Database session (injected for testing)
        min_articles: Minimum number of recent articles to analyze

    Returns:
        Number of new frameworks created
    """
    if not openai_client.is_available():
        logger.error("OpenAI API not configured")
        return 0

    created_count = 0

    # Get recent analyzed articles (last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)

    recent_articles = session.exec(
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(Article.scraped_at >= week_ago)
        .limit(min_articles)
    ).all()

    if len(recent_articles) < min_articles:
        logger.warning(
            f"Not enough recent articles ({len(recent_articles)}) to discover frameworks"
        )
        return 0

    logger.info(f"Analyzing {len(recent_articles)} recent articles for new frameworks...")

    # Get existing framework names to avoid duplicates
    existing_frameworks = session.exec(select(Framework)).all()
    existing_names = [fw.name for fw in existing_frameworks]

    # Build summary of articles
    article_summaries = []
    for article, analysis in recent_articles[:30]:  # Limit to 30 for token economy
        article_summaries.append(f"{article.title}: {analysis.summary[:200]}")

    # Ask OpenAI to identify new frameworks
    try:
        new_frameworks = openai_client.generate_frameworks(
            article_summaries,
            existing_names
        )

        if not new_frameworks:
            logger.warning("No new frameworks generated")
            return 0

        # Create new framework records
        for fw_data in new_frameworks:
            framework = Framework(
                name=fw_data.get('name', '')[:200],
                description=fw_data.get('description', '')[:1000],
                axis_description=fw_data.get('axis_description', '')[:200],
                left_position=fw_data.get('left_position', '')[:200],
                right_position=fw_data.get('right_position', '')[:200],
                article_count=0,
                last_active=datetime.utcnow(),
                created_at=datetime.utcnow(),
                is_seed=False  # AI-generated, not hand-curated
            )

            session.add(framework)
            created_count += 1

            logger.info(f"  ✓ Created new framework: {framework.name}")

        session.commit()
        logger.info(f"Discovered {created_count} new frameworks")

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse framework discovery response: {e}")
    except Exception as e:
        logger.error(f"Error discovering frameworks: {e}", exc_info=True)

    return created_count


def _build_framework_mapping_prompt(
    title: str,
    summary: str,
    frameworks: Dict[int, Dict]
) -> str:
    """Build prompt for mapping an article to frameworks"""

    frameworks_list = ""
    for fw_id, fw_info in frameworks.items():
        frameworks_list += f"\n{fw_id}. {fw_info['name']}\n"
        frameworks_list += f"   {fw_info['description']}\n"
        frameworks_list += f"   Axis: {fw_info['axis']}\n"

    prompt = f"""Given this news article, identify which ethical/philosophical frameworks it relates to (if any).

Article Title: {title}

Article Summary: {summary}

Available Frameworks:
{frameworks_list}

For each relevant framework (up to 3), provide:
1. framework_id (the number from the list)
2. relevance_score (0.0 to 1.0, how strongly this article relates)
3. position (-10 to +10, where -10 is far left on the axis, +10 is far right)
4. explanation (1-2 sentences explaining the connection)

Return as JSON array. If no frameworks are relevant, return empty array [].

Example:
[
  {{
    "framework_id": 1,
    "relevance_score": 0.85,
    "position": -6,
    "explanation": "This policy prioritizes collective welfare over individual autonomy."
  }}
]

Return ONLY the JSON array, no other text."""

    return prompt


def _build_framework_discovery_prompt(
    article_summaries: List[Dict],
    existing_names: List[str]
) -> str:
    """Build prompt for discovering new frameworks"""

    articles_text = ""
    for i, article in enumerate(article_summaries[:20], 1):
        articles_text += f"\n{i}. {article['title']}\n"
        articles_text += f"   {article['summary'][:200]}...\n"

    existing_text = ", ".join(existing_names)

    prompt = f"""Analyze these recent news articles and identify 1-3 NEW underlying ethical/philosophical debates that emerge.

These debates should:
- Be distinct from existing frameworks: {existing_text}
- Represent genuine tensions with two opposing positions
- Be relevant to multiple articles (not just one)
- Be expressible as a spectrum or axis

Articles:
{articles_text}

For each new framework, provide:
1. name: Clear, concise name for the debate
2. description: What this debate is about (1-2 sentences)
3. axis_description: Short axis label (e.g., "individual freedom ←→ social responsibility")
4. left_position: One side of the debate
5. right_position: Opposing side

Return as JSON array. If no new frameworks are apparent, return empty array [].

Example:
[
  {{
    "name": "Algorithmic Efficiency vs. Human Autonomy",
    "description": "The tension between using AI/algorithms for optimal decisions versus preserving human agency and choice",
    "axis_description": "algorithmic optimization ←→ human control",
    "left_position": "Embrace AI-driven optimization for better outcomes",
    "right_position": "Preserve human decision-making authority"
  }}
]

Return ONLY the JSON array, no other text."""

    return prompt


if __name__ == "__main__":
    # Test mapping
    with Session(engine) as session:
        count = map_articles_to_frameworks(session, limit=5)
        print(f"Created {count} framework mappings")
