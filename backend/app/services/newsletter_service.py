"""
Newsletter generation and sending service using Resend.
Generates personalized newsletters based on user preferences and sends via email.
"""

from sqlmodel import Session, select
from app.models import (
    User, Article, ArticleAnalysis, Framework, ArticleFrameworkLink,
    UserTopicPreference, Newsletter, NewsletterArticle, Topic,
    StatisticVerification, ArticleContext, ArticleCluster, ArticleClusterMember
)
from app.database import engine
from app.config import settings
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from jinja2 import Template, Environment, FileSystemLoader
import os
import resend
import json

logger = logging.getLogger(__name__)

# Initialize Resend
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    logger.warning("RESEND_API_KEY not set - email sending will be disabled")


def generate_and_send_newsletters(session: Session = None) -> Dict[str, int]:
    """
    Generate and send personalized newsletters to all active users.

    Args:
        session: Optional database session (for testing). If None, creates new session.

    Returns:
        Dict with counts of newsletters generated, sent, and failed
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured - cannot send newsletters")
        return {"generated": 0, "sent": 0, "failed": 0}

    stats = {"generated": 0, "sent": 0, "failed": 0}

    def _generate(session: Session):
        """Inner function to generate newsletters with provided session"""
        # Get all active users with email verified
        active_users = session.exec(
            select(User)
            .where(User.is_active == True)
            .where(User.email_verified == True)
        ).all()

        if not active_users:
            logger.info("No active users to send newsletters to")
            return stats

        logger.info(f"Generating newsletters for {len(active_users)} users...")

        for user in active_users:
            try:
                # Generate newsletter content
                newsletter_data = _generate_newsletter_for_user(user, session)

                if not newsletter_data:
                    logger.warning(f"No content for user {user.email}")
                    continue

                # Create newsletter record
                newsletter = Newsletter(
                    user_id=user.id,
                    subject=f"Your Pulse News Digest - {datetime.utcnow().strftime('%B %d, %Y')}",
                    html_content=newsletter_data["html"],
                    sent_at=None  # Will be set after successful send
                )
                session.add(newsletter)
                session.flush()  # Get newsletter.id

                # Link articles to newsletter
                for article_id in newsletter_data["article_ids"]:
                    newsletter_article = NewsletterArticle(
                        newsletter_id=newsletter.id,
                        article_id=article_id
                    )
                    session.add(newsletter_article)

                stats["generated"] += 1

                # Send email via Resend
                try:
                    response = resend.Emails.send({
                        "from": f"{settings.from_name} <{settings.from_email}>",
                        "to": user.email,
                        "subject": newsletter.subject,
                        "html": newsletter.html_content
                    })

                    # Mark as sent
                    newsletter.sent_at = datetime.utcnow()
                    session.commit()

                    stats["sent"] += 1
                    logger.info(f"✓ Sent newsletter to {user.email}")

                except Exception as e:
                    logger.error(f"Failed to send email to {user.email}: {e}")
                    stats["failed"] += 1
                    session.rollback()
                    continue

            except Exception as e:
                logger.error(f"Error generating newsletter for user {user.id}: {e}", exc_info=True)
                stats["failed"] += 1
                session.rollback()
                continue

        logger.info(
            f"Newsletter job complete: {stats['generated']} generated, "
            f"{stats['sent']} sent, {stats['failed']} failed"
        )
        return stats

    # Use provided session or create new one
    if session is not None:
        return _generate(session)
    else:
        with Session(engine) as session:
            return _generate(session)


def _generate_newsletter_for_user(user: User, session: Session) -> Optional[Dict]:
    """
    Generate newsletter content for a specific user based on their preferences.

    Returns:
        Dict with 'html' and 'article_ids' or None if no content available
    """
    # Get user's preferred topics
    user_preferences = session.exec(
        select(UserTopicPreference)
        .where(UserTopicPreference.user_id == user.id)
        .where(UserTopicPreference.include_in_newsletter == True)
    ).all()

    preferred_topic_ids = [pref.topic_id for pref in user_preferences]

    if not preferred_topic_ids:
        # If no preferences, use all topics (fallback)
        all_topics = session.exec(select(Topic)).all()
        preferred_topic_ids = [topic.id for topic in all_topics]


    # OLD WAY (commented):
    # yesterday = datetime.utcnow() - timedelta(hours=24)
    # articles_query = (
    #     select(Article, ArticleAnalysis)
    #     .join(ArticleAnalysis)
    #     .where(Article.scraped_at >= yesterday)
    #     .where(Article.topics.any(Topic.id.in_(preferred_topic_ids)))
    #     .order_by(Article.scraped_at.desc())
    #     .limit(settings.max_articles_per_newsletter)
    # )
    # articles_with_analysis = session.exec(articles_query).all()

    # NEW WAY: select random articles with analysis
    from sqlalchemy import func
    articles_query = (
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .order_by(func.random())
        .limit(settings.max_articles_per_newsletter)
    )
    articles_with_analysis = session.exec(articles_query).all()

    if not articles_with_analysis:
        logger.warning(f"No articles found for user {user.email}")
        return None

    # Get frameworks related to these articles
    article_ids = [article.id for article, _ in articles_with_analysis]

    framework_links = session.exec(
        select(ArticleFrameworkLink, Framework)
        .join(Framework)
        .where(ArticleFrameworkLink.article_id.in_(article_ids))
        .where(ArticleFrameworkLink.relevance_score >= 0.5)
        .order_by(ArticleFrameworkLink.relevance_score.desc())
    ).all()

    # Group frameworks and count articles
    framework_data = {}
    for link, framework in framework_links:
        if framework.id not in framework_data:
            framework_data[framework.id] = {
                "framework": framework,
                "article_count": 0
            }
        framework_data[framework.id]["article_count"] += 1

    # Take top frameworks
    top_frameworks = sorted(
        framework_data.values(),
        key=lambda x: x["article_count"],
        reverse=True
    )[:settings.max_frameworks_per_newsletter]

    # Prepare template data
    template_data = {
        "user_name": user.name or "there",
        "date": datetime.utcnow().strftime("%B %d, %Y"),
        "article_count": len(articles_with_analysis),
        "framework_count": len(top_frameworks),
        "frameworks": [
            {
                "name": fw["framework"].name,
                "description": fw["framework"].description,
                "left_position": fw["framework"].left_position,
                "right_position": fw["framework"].right_position,
                "article_count": fw["article_count"]
            }
            for fw in top_frameworks
        ],
        "articles": [],
        "preferences_url": f"https://pulse.news/preferences?token={user.email}",  # TODO: Add real token
        "website_url": "https://pulse.news",
        "unsubscribe_url": f"https://pulse.news/unsubscribe?token={user.email}"  # TODO: Add real token
    }

    # Add article data with enhancements
    for article, analysis in articles_with_analysis:
        # Get statistics with verification
        statistics = session.exec(
            select(StatisticVerification)
            .where(StatisticVerification.article_id == article.id)
        ).all()

        # Get context if available
        context = session.exec(
            select(ArticleContext)
            .where(ArticleContext.article_id == article.id)
        ).first()

        # Get framework mappings for this article
        framework_mappings = session.exec(
            select(ArticleFrameworkLink, Framework)
            .join(Framework)
            .where(ArticleFrameworkLink.article_id == article.id)
            .where(ArticleFrameworkLink.relevance_score >= 0.6)  # Only strong matches
            .order_by(ArticleFrameworkLink.relevance_score.desc())
            .limit(2)  # Max 2 frameworks per article
        ).all()

        frameworks_for_article = []
        for link, framework in framework_mappings:
            frameworks_for_article.append({
                "name": framework.name,
                "left_position": framework.left_position,
                "right_position": framework.right_position,
                "position_on_axis": link.position_on_axis,  # -10 to +10
                "relevance_score": link.relevance_score,
                "explanation": link.ai_explanation
            })

        # Get cluster information
        cluster_member = session.exec(
            select(ArticleClusterMember, ArticleCluster)
            .join(ArticleCluster)
            .where(ArticleClusterMember.article_id == article.id)
        ).first()

        cluster_info = None
        if cluster_member:
            member, cluster = cluster_member
            # Get other articles in the same cluster
            other_members = session.exec(
                select(ArticleClusterMember, Article)
                .join(Article)
                .where(ArticleClusterMember.cluster_id == cluster.id)
                .where(ArticleClusterMember.article_id != article.id)
            ).all()

            cluster_info = {
                "topic": cluster.primary_topic,
                "article_count": len(other_members) + 1,
                "other_sources": [
                    {"source": other_article.source.name, "url": other_article.url}
                    for _, other_article in other_members[:3]  # Limit to 3
                ]
            }

        template_data["articles"].append({
            "title": article.title,
            "url": article.url,
            "source_name": article.source.name,
            "political_lean": analysis.political_lean.value if analysis.political_lean else None,
            "published_at": article.published_at.strftime("%b %d") if article.published_at else "",
            "summary": analysis.summary,
            "key_stats": analysis.key_stats,
            "frameworks": frameworks_for_article,
            "statistics": [
                {
                    "text": stat.statistic_text,
                    "context": stat.context,
                    "status": stat.verification_status.value,
                    "confidence": stat.confidence_score,
                    # V2 fields
                    "source_name": stat.source_name,
                    "source_url": stat.source_url,
                    "source_credibility_score": stat.source_credibility_score,
                    "fact_check_status": stat.fact_check_status,
                    "fact_check_source": stat.fact_check_source,
                    "fact_check_url": stat.fact_check_url,
                    "fact_check_details": stat.fact_check_details
                }
                for stat in statistics
            ],
            "context": {
                "background": context.background,
                "key_players": json.loads(context.key_players) if context.key_players else [],
                "timeline": json.loads(context.timeline) if context.timeline else [],
                "significance": context.significance,
                "next_developments": context.next_developments
            } if context else None,
            "cluster": cluster_info
        })

    # Render template
    html_content = _render_newsletter_template(template_data)

    return {
        "html": html_content,
        "article_ids": article_ids
    }


def _render_newsletter_template(data: Dict) -> str:
    """Render the newsletter HTML template with provided data"""

    # Get template directory
    template_dir = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "templates"
    )

    # Load template
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template("newsletter.html")

    # Render
    html = template.render(**data)

    return html


def send_test_newsletter(user_email: str) -> bool:
    """
    Send a test newsletter to a specific email address.
    Useful for testing before going live.

    Returns:
        True if sent successfully, False otherwise
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured")
        return False

    with Session(engine) as session:
        user = session.exec(
            select(User).where(User.email == user_email)
        ).first()

        if not user:
            logger.error(f"User not found: {user_email}")
            return False

        newsletter_data = _generate_newsletter_for_user(user, session)

        if not newsletter_data:
            logger.error(f"Could not generate newsletter for {user_email}")
            return False

        try:
            response = resend.Emails.send({
                "from": f"{settings.from_name} <{settings.from_email}>",
                "to": user_email,
                "subject": f"[TEST] Your Pulse News Digest - {datetime.utcnow().strftime('%B %d, %Y')}",
                "html": newsletter_data["html"]
            })

            logger.info(f"Test newsletter sent to {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send test newsletter: {e}", exc_info=True)
            return False


if __name__ == "__main__":
    # Test newsletter generation
    stats = generate_and_send_newsletters()
    print(f"Newsletters: {stats['generated']} generated, {stats['sent']} sent, {stats['failed']} failed")
