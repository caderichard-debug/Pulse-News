"""
Source Tracer Service

Traces statistics to their original sources using multiple methods:
1. Within article content (AI extraction + URL parsing)
2. Web search for the statistic
3. Cross-article database search
"""

import re
import json
import logging
import requests
from typing import Optional, Dict, List
from urllib.parse import urlparse, quote
from sqlmodel import Session, select

from app.models import Article, StatisticVerification
from app.config import settings
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
openai_api = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

TRACE_SOURCE_PROMPT = """Given this article content and a specific statistic, identify the original source.

Article URL: {article_url}
Statistic: "{statistic_text}"

Article Content:
{article_content}

Identify:
1. source_url: URL of the original source (if mentioned in the article)
2. source_name: Name of organization/publication that produced the statistic
3. source_excerpt: The exact text from the article that mentions the source
4. confidence: Your confidence in this identification (0.0 to 1.0)

Return JSON:
{{
  "source_url": "https://...",
  "source_name": "Organization Name",
  "source_excerpt": "According to a Johns Hopkins study...",
  "confidence": 0.85
}}

If no source is identifiable, return null for the URL and name fields but still provide the best guess:
{{
  "source_url": null,
  "source_name": null,
  "source_excerpt": "The article doesn't cite a specific source for this statistic",
  "confidence": 0.0
}}
"""


class SourceTracer:
    """Service for tracing statistics to their original sources."""

    def __init__(self):
        self.openai_api = openai_api

    def trace_statistic_source(
        self,
        statistic_text: str,
        article_content: str,
        article_url: str,
        session: Session = None
    ) -> Optional[Dict]:
        """
        Trace a statistic to its original source using multiple methods.

        Priority order:
        1. Within article content (AI + URL extraction)
        2. Web search for the statistic
        3. Cross-article database search

        Args:
            statistic_text: The statistic to trace
            article_content: Full article text
            article_url: URL of the article
            session: Database session (optional)

        Returns:
            Dict with keys: source_url, source_name, source_excerpt, confidence, method
            Returns None if all tracing methods fail
        """
        try:
            # Method 1: Try to find source within the article
            result = self._trace_within_article(statistic_text, article_content, article_url)

            if result and result.get("source_name"):
                result["method"] = "article_content"
                logger.info(f"Found source in article: {result.get('source_name')}")
                return result

            # Method 2: Try web search
            if settings.google_fact_check_api_key:  # Reuse the Google API key if available
                web_result = self._trace_via_web_search(statistic_text)
                if web_result and web_result.get("source_name"):
                    web_result["method"] = "web_search"
                    logger.info(f"Found source via web search: {web_result.get('source_name')}")
                    return web_result

            # Method 3: Try cross-article database search
            if session:
                db_result = self._trace_via_database(statistic_text, session)
                if db_result and db_result.get("source_name"):
                    db_result["method"] = "database_search"
                    logger.info(f"Found source in database: {db_result.get('source_name')}")
                    return db_result

            # If we have a partial result from article (no source name), return it
            if result:
                result["method"] = "article_content"
                return result

            return None

        except Exception as e:
            logger.error(f"Error tracing source for statistic '{statistic_text[:50]}': {e}")
            return None

    def _trace_within_article(
        self,
        statistic_text: str,
        article_content: str,
        article_url: str
    ) -> Optional[Dict]:
        """Trace source within the article content (original method)."""
        try:
            # Step 1: Try to find URLs near the statistic in the text
            nearby_urls = self._extract_nearby_urls(statistic_text, article_content)

            # Step 2: Use AI to identify source mentions
            ai_result = self._ai_extract_source(statistic_text, article_content, article_url)

            if not ai_result:
                return None

            # Step 3: Combine results - prefer AI-identified URL over nearby URLs
            result = ai_result

            # If AI didn't find a URL but we found nearby URLs, use the first one
            if not result.get("source_url") and nearby_urls:
                result["source_url"] = nearby_urls[0]
                result["confidence"] = min(result.get("confidence", 0.5), 0.6)

            return result

        except Exception as e:
            logger.error(f"Error in article source trace: {e}")
            return None

    def _extract_nearby_urls(self, statistic_text: str, article_content: str, window: int = 500) -> List[str]:
        """
        Extract URLs that appear near the statistic in the article text.

        Args:
            statistic_text: The statistic to search for
            article_content: Full article text
            window: Characters before/after to search for URLs

        Returns:
            List of URLs found near the statistic
        """
        try:
            # Find position of statistic in content
            stat_lower = statistic_text.lower()
            content_lower = article_content.lower()

            position = content_lower.find(stat_lower)
            if position == -1:
                # Try to find a partial match (first 30 chars)
                if len(stat_lower) > 30:
                    position = content_lower.find(stat_lower[:30])

            if position == -1:
                return []

            # Extract window around the statistic
            start = max(0, position - window)
            end = min(len(article_content), position + len(statistic_text) + window)
            context = article_content[start:end]

            # Find URLs in the context
            url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+[^\s.,;!?\'")\]}>]'
            urls = re.findall(url_pattern, context)

            # Filter out common non-source URLs (social media, analytics, etc.)
            filtered_urls = []
            exclude_domains = ['twitter.com', 'facebook.com', 'instagram.com', 'linkedin.com',
                             'youtube.com', 'google-analytics.com', 't.co', 'bit.ly']

            for url in urls:
                domain = urlparse(url).netloc.lower()
                if not any(excluded in domain for excluded in exclude_domains):
                    filtered_urls.append(url)

            return filtered_urls

        except Exception as e:
            logger.error(f"Error extracting nearby URLs: {e}")
            return []

    def _ai_extract_source(
        self,
        statistic_text: str,
        article_content: str,
        article_url: str
    ) -> Optional[Dict]:
        """
        Use AI to extract source information from article content.

        Args:
            statistic_text: The statistic to trace
            article_content: Full article text
            article_url: URL of the article

        Returns:
            Dict with source info or None if extraction fails
        """
        if not self.openai_api:
            logger.warning("OpenAI API key not configured - cannot extract source")
            return None

        try:
            # Truncate content if too long (keep first 3000 chars for context)
            if len(article_content) > 3000:
                article_content = article_content[:3000] + "..."

            prompt = TRACE_SOURCE_PROMPT.format(
                article_url=article_url,
                statistic_text=statistic_text,
                article_content=article_content
            )

            response = self.openai_api.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert at identifying sources and citations in articles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            content = response.choices[0].message.content.strip()

            # Parse JSON response
            # Handle markdown code blocks if present
            if content.startswith("```"):
                content = content.split("```")[1]
                if content.startswith("json"):
                    content = content[4:]
            content = content.strip()

            result = json.loads(content)

            # Validate result structure
            if not isinstance(result, dict):
                logger.error(f"AI returned non-dict result: {result}")
                return None

            # Ensure confidence is set
            if "confidence" not in result:
                result["confidence"] = 0.5

            logger.info(
                f"AI extracted source: {result.get('source_name', 'Unknown')} "
                f"(confidence: {result.get('confidence', 0.0):.2f})"
            )

            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            logger.debug(f"AI response content: {content}")
            return None
        except Exception as e:
            logger.error(f"Error in AI source extraction: {e}")
            return None


    def _trace_via_web_search(self, statistic_text: str) -> Optional[Dict]:
        """
        Trace source via web search using Google Custom Search API.

        Args:
            statistic_text: The statistic to search for

        Returns:
            Dict with source info or None
        """
        if not settings.google_fact_check_api_key:
            return None

        try:
            # Use Google Custom Search API to search for the statistic
            search_query = f'"{statistic_text}" source study report'
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": settings.google_fact_check_api_key,
                "cx": settings.google_search_engine_id if hasattr(settings, 'google_search_engine_id') else None,
                "q": search_query,
                "num": 3  # Get top 3 results
            }

            if not params["cx"]:
                logger.debug("Google Custom Search Engine ID not configured")
                return None

            response = requests.get(url, params=params, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Google Search API returned status {response.status_code}")
                return None

            data = response.json()

            if not data.get("items"):
                return None

            # Analyze top result
            top_result = data["items"][0]
            source_url = top_result.get("link", "")
            title = top_result.get("title", "")
            snippet = top_result.get("snippet", "")

            # Use AI to extract source name from title/snippet
            source_name = self._extract_source_name_from_search(title, snippet, source_url)

            return {
                "source_url": source_url,
                "source_name": source_name,
                "source_excerpt": snippet[:200],
                "confidence": 0.7  # Medium-high confidence for web search
            }

        except Exception as e:
            logger.error(f"Error in web search trace: {e}")
            return None

    def _trace_via_database(self, statistic_text: str, session: Session) -> Optional[Dict]:
        """
        Trace source by finding the same statistic in other articles in our database.

        Args:
            statistic_text: The statistic to search for
            session: Database session

        Returns:
            Dict with source info or None
        """
        try:
            # Search for statistics with similar text in our database
            all_stats = session.exec(
                select(StatisticVerification)
                .where(StatisticVerification.source_name.isnot(None))
            ).all()

            # Look for similar statistics
            stat_lower = statistic_text.lower()
            for other_stat in all_stats:
                if other_stat.statistic_text.lower() in stat_lower or stat_lower in other_stat.statistic_text.lower():
                    # Found a match!
                    return {
                        "source_url": other_stat.source_url,
                        "source_name": other_stat.source_name,
                        "source_excerpt": f"Found in another article: {other_stat.source_excerpt[:100] if other_stat.source_excerpt else ''}",
                        "confidence": 0.65  # Medium confidence for cross-reference
                    }

            return None

        except Exception as e:
            logger.error(f"Error in database trace: {e}")
            return None

    def _extract_source_name_from_search(self, title: str, snippet: str, url: str) -> Optional[str]:
        """Extract source name from search result using heuristics."""
        # Extract domain
        domain = urlparse(url).netloc
        if domain.startswith("www."):
            domain = domain[4:]

        # Look for known patterns in title/snippet
        patterns = [
            r"(?:according to|from|by|study by|report by)\s+([A-Z][A-Za-z\s&]+(?:University|Institute|Bureau|Agency|Department|Foundation|Center|Association))",
            r"([A-Z][A-Za-z\s&]+(?:University|Institute|Bureau|Agency|Department|Foundation|Center|Association))",
        ]

        for pattern in patterns:
            match = re.search(pattern, title + " " + snippet)
            if match:
                return match.group(1).strip()

        # Fallback to domain name
        return domain.split(".")[0].title()


# Singleton instance
_source_tracer = None


def get_source_tracer() -> SourceTracer:
    """Get singleton instance of SourceTracer."""
    global _source_tracer
    if _source_tracer is None:
        _source_tracer = SourceTracer()
    return _source_tracer
