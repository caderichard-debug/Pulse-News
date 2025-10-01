"""
Newsletter generation and sending service using Resend.
Generates personalized newsletters based on user preferences and sends via email.
"""

from sqlmodel import Session, select
from app.models import (
    User, Article, ArticleAnalysis, Framework, ArticleFrameworkLink,
    UserTopicPreference, Newsletter, NewsletterArticle, Topic
)
from app.database import engine
from app.config import settings
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging
from jinja2 import Template, Environment, FileSystemLoader
import os
import resend

logger = logging.getLogger(__name__)

# Initialize Resend
if settings.resend_api_key:
    resend.api_key = settings.resend_api_key
else:
    logger.warning("RESEND_API_KEY not set - email sending will be disabled")


def generate_and_send_newsletters() -> Dict[str, int]:
    """
    Generate and send personalized newsletters to all active users.

    Returns:
        Dict with counts of newsletters generated, sent, and failed
    """
    if not settings.resend_api_key:
        logger.error("Resend API key not configured - cannot send newsletters")
        return {"generated": 0, "sent": 0, "failed": 0}

    stats = {"generated": 0, "sent": 0, "failed": 0}

    with Session(engine) as session:
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
        .where(UserTopicPreference.is_active == True)
    ).all()

    preferred_topic_ids = [pref.topic_id for pref in user_preferences]

    if not preferred_topic_ids:
        # If no preferences, use all topics (fallback)
        all_topics = session.exec(select(Topic)).all()
        preferred_topic_ids = [topic.id for topic in all_topics]

    # Get recent analyzed articles from preferred topics (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(hours=24)

    articles_query = (
        select(Article, ArticleAnalysis)
        .join(ArticleAnalysis)
        .where(Article.scraped_at >= yesterday)
        .where(Article.topics.any(Topic.id.in_(preferred_topic_ids)))
        .order_by(Article.scraped_at.desc())
        .limit(settings.max_articles_per_newsletter)
    )

    articles_with_analysis = session.exec(articles_query).all()

    if not articles_with_analysis:
        logger.warning(f"No recent articles found for user {user.email}")
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

    # Add article data
    for article, analysis in articles_with_analysis:
        # Get source name
        source_name = session.get(article.__class__, article.id).source.name if hasattr(article, 'source') else "Unknown"

        template_data["articles"].append({
            "title": article.title,
            "url": article.url,
            "source_name": article.source.name,
            "political_lean": analysis.political_lean.value if analysis.political_lean else None,
            "published_at": article.published_at.strftime("%b %d") if article.published_at else "",
            "summary": analysis.summary,
            "key_stats": analysis.key_stats
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
