"""
Service for analyzing articles from user-submitted URLs.
Orchestrates extraction, AI analysis, framework generation, statistics verification, and context generation.
"""

from typing import Optional, Dict, Any
from sqlmodel import Session, select
import httpx
from urllib.parse import urlparse
import logging
from datetime import datetime

from ..models import (
    Article, Source, User, ArticleAnalysis, Framework,
    ArticleFrameworkLink, StatisticVerification, ArticleContext,
    ProcessingStatus, PoliticalLean, Topic, ArticleTopicLink
)
from ..services.article_extractor import extract_article_content
from ..utils.openai_client import openai_client
from ..services.framework_generator import map_articles_to_frameworks
from ..services.statistics_verifier import extract_statistics_from_article
from ..services.context_generator import generate_article_context

logger = logging.getLogger(__name__)


class URLAnalyzer:
    """Analyzes articles from user-submitted URLs."""

    def __init__(self, db: Session):
        self.db = db

    async def analyze_url(
        self,
        url: str,
        user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Analyze an article from a URL.

        Args:
            url: Article URL to analyze
            user_id: Optional user ID if authenticated

        Returns:
            Dictionary containing article data and all analysis results

        Raises:
            ValueError: If URL is invalid or inaccessible
            Exception: If extraction or analysis fails
        """
        # Step 1: Validate URL
        logger.info(f"Starting analysis for URL: {url}")
        await self._validate_url(url)

        # Step 2: Check if article already exists (by URL)
        existing_article = self.db.exec(
            select(Article).where(Article.url == url)
        ).first()

        if existing_article:
            logger.info(f"Article already exists with ID {existing_article.id}")
            # Ensure all analysis is complete
            if not existing_article.analysis:
                await self._complete_analysis(existing_article)
            response = self._format_response(existing_article)
            response['already_existed'] = True
            return response

        # Step 3: Extract article content
        logger.info("Extracting article content...")
        extraction_result = extract_article_content(url)

        if not extraction_result.get('success') or not extraction_result.get('content'):
            raise ValueError("Failed to extract article content. The article may be behind a paywall or the URL may be inaccessible.")

        # Step 4: Get or create source
        source = self._get_or_create_source(url, extraction_result)

        # Step 5: Create article record
        article = Article(
            title=extraction_result.get('title', 'Untitled'),
            url=url,
            content_text=extraction_result['content'],
            author=extraction_result.get('author'),
            published_at=extraction_result.get('published_date', datetime.utcnow()),
            source_id=source.id,
            is_user_submitted=True,
            submitted_by_user_id=user_id,
            processing_status=ProcessingStatus.COMPLETED,
            extraction_method=extraction_result.get('method'),
            word_count=extraction_result.get('word_count')
        )
        self.db.add(article)
        self.db.commit()
        self.db.refresh(article)
        logger.info(f"Created article with ID {article.id}")

        # Step 6: Complete all analysis steps
        await self._complete_analysis(article)

        # Refresh and return
        self.db.refresh(article)
        return self._format_response(article)

    async def _complete_analysis(self, article: Article):
        """Complete all analysis steps for an article."""
        # Step 1: AI Analysis
        if not article.analysis:
            logger.info(f"Performing AI analysis for article {article.id}...")
            await self._perform_ai_analysis(article)
            self.db.refresh(article)

        # Step 2: Framework Generation
        framework_links = self.db.exec(
            select(ArticleFrameworkLink).where(ArticleFrameworkLink.article_id == article.id)
        ).first()

        if not framework_links:
            logger.info(f"Generating ethical frameworks for article {article.id}...")
            map_articles_to_frameworks(self.db, article_ids=[article.id])

        # Step 3: Statistics Verification
        statistics = self.db.exec(
            select(StatisticVerification).where(StatisticVerification.article_id == article.id)
        ).first()

        if not statistics and article.analysis:
            logger.info(f"Verifying statistics for article {article.id}...")
            stats = extract_statistics_from_article(article, article.analysis, self.db)
            for stat in stats:
                self.db.add(stat)
            self.db.commit()

        # Step 4: Context Generation
        context = self.db.exec(
            select(ArticleContext).where(ArticleContext.article_id == article.id)
        ).first()

        if not context and article.analysis:
            logger.info(f"Generating context for article {article.id}...")
            ctx = generate_article_context(article, article.analysis, self.db)
            if ctx:
                self.db.add(ctx)
                self.db.commit()

        logger.info(f"Analysis complete for article {article.id}!")

    async def _perform_ai_analysis(self, article: Article):
        """Perform AI analysis on an article."""
        if not openai_client.is_available():
            logger.warning("OpenAI API not configured, skipping AI analysis")
            return

        # Call OpenAI API for single article
        article_data = [{
            "title": article.title,
            "content": article.content_text
        }]

        analyses = openai_client.analyze_articles_batch(article_data)

        if not analyses or len(analyses) == 0:
            logger.error("Failed to get analysis from OpenAI")
            return

        analysis_data = analyses[0]

        # Map political lean
        lean_str = analysis_data.get('political_lean', 'center').lower()
        try:
            political_lean = next(
                (lean for lean in PoliticalLean if lean.value == lean_str),
                PoliticalLean.CENTER
            )
        except StopIteration:
            political_lean = PoliticalLean.CENTER

        # Create analysis record
        article_analysis = ArticleAnalysis(
            article_id=article.id,
            summary=analysis_data.get('summary', ''),
            sentiment_score=analysis_data.get('sentiment_score', 0.0),
            political_lean=political_lean,
            analyzed_at=datetime.utcnow()
        )
        self.db.add(article_analysis)
        self.db.commit()

    async def _validate_url(self, url: str) -> None:
        """Validate URL format and accessibility."""
        # Parse URL
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format. Please provide a complete URL (e.g., https://example.com/article)")
        except Exception as e:
            raise ValueError(f"Invalid URL: {str(e)}")

        # Check accessibility (HEAD request with timeout)
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.head(url)
                if response.status_code >= 400:
                    # Try GET request as some servers don't support HEAD
                    response = await client.get(url)
                    if response.status_code >= 400:
                        raise ValueError(f"URL returned status code {response.status_code}")
        except httpx.TimeoutException:
            raise ValueError("URL request timed out. Please check the URL and try again.")
        except httpx.RequestError as e:
            raise ValueError(f"Failed to access URL: {str(e)}")

    def _get_or_create_source(
        self,
        url: str,
        extraction_result: Dict[str, Any]
    ) -> Source:
        """Get existing source or create a new one."""
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Check if source exists
        source = self.db.exec(
            select(Source).where(Source.url == domain)
        ).first()

        if source:
            return source

        # Create new source
        # Use a dummy RSS feed URL for user-submitted sources
        source = Source(
            name=extraction_result.get("site_name", parsed.netloc),
            url=domain,
            rss_feed_url=f"{domain}/rss",  # Dummy RSS URL (won't be used)
            description=f"User-submitted source from {parsed.netloc}",
            trust_score=0.5  # Default neutral trust score
        )
        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)
        return source

    def _format_response(self, article: Article) -> Dict[str, Any]:
        """Format article with all analysis data for API response."""
        response = {
            "id": article.id,
            "title": article.title,
            "url": article.url,
            "content": article.content_text,
            "author": article.author,
            "published_date": article.published_at.isoformat() if article.published_at else None,
            "word_count": article.word_count,
            "source": None,
            "is_user_submitted": article.is_user_submitted,
            "analysis": None,
            "frameworks": [],
            "statistics": [],
            "context": None
        }

        # Add source data
        if article.source:
            response["source"] = {
                "id": article.source.id,
                "name": article.source.name,
                "url": article.source.url,
                "trust_score": article.source.trust_score
            }

        # Add analysis data
        if article.analysis:
            response["analysis"] = {
                "summary": article.analysis.summary,
                "sentiment_score": article.analysis.sentiment_score,
                "political_lean": article.analysis.political_lean.value if article.analysis.political_lean else None
            }

        # Add frameworks
        framework_links = self.db.exec(
            select(ArticleFrameworkLink)
            .where(ArticleFrameworkLink.article_id == article.id)
        ).all()

        if framework_links:
            response["frameworks"] = [
                {
                    "id": link.framework_id,
                    "name": self.db.get(Framework, link.framework_id).name if self.db.get(Framework, link.framework_id) else None,
                    "description": self.db.get(Framework, link.framework_id).description if self.db.get(Framework, link.framework_id) else None,
                    "relevance_score": link.relevance_score,
                    "position_on_axis": link.position_on_axis,
                    "ai_explanation": link.ai_explanation
                }
                for link in framework_links
            ]

        # Add statistics
        statistics = self.db.exec(
            select(StatisticVerification)
            .where(StatisticVerification.article_id == article.id)
        ).all()

        if statistics:
            response["statistics"] = [
                {
                    "id": stat.id,
                    "claim_text": stat.statistic_text,
                    "verification_status": stat.verification_status.value if stat.verification_status else None,
                    "source_url": stat.source_url,
                    "source_name": stat.source_name,
                    "credibility_score": stat.source_credibility_score
                }
                for stat in statistics
            ]

        # Add context
        context = self.db.exec(
            select(ArticleContext)
            .where(ArticleContext.article_id == article.id)
        ).first()

        if context:
            response["context"] = {
                "background": context.background_context,
                "timeline": context.timeline_context,
                "significance": context.significance_analysis
            }

        return response
