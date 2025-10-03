"""
Source Tracer Service

Traces statistics to their original sources within article content.
Uses AI to identify source mentions and extract URLs/citations.
"""

import re
import json
import logging
from typing import Optional, Dict, List
from urllib.parse import urlparse
from sqlmodel import Session

from app.models import Article
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
        Trace a statistic to its original source within an article.

        Args:
            statistic_text: The statistic to trace
            article_content: Full article text
            article_url: URL of the article
            session: Database session (optional)

        Returns:
            Dict with keys: source_url, source_name, source_excerpt, confidence
            Returns None if tracing fails
        """
        try:
            # Step 1: Try to find URLs near the statistic in the text
            nearby_urls = self._extract_nearby_urls(statistic_text, article_content)

            # Step 2: Use AI to identify source mentions
            ai_result = self._ai_extract_source(statistic_text, article_content, article_url)

            if not ai_result:
                logger.warning(f"AI source extraction failed for statistic: {statistic_text[:50]}")
                return None

            # Step 3: Combine results - prefer AI-identified URL over nearby URLs
            result = ai_result

            # If AI didn't find a URL but we found nearby URLs, use the first one
            if not result.get("source_url") and nearby_urls:
                result["source_url"] = nearby_urls[0]
                result["confidence"] = min(result.get("confidence", 0.5), 0.6)  # Lower confidence

            return result

        except Exception as e:
            logger.error(f"Error tracing source for statistic '{statistic_text[:50]}': {e}")
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


# Singleton instance
_source_tracer = None


def get_source_tracer() -> SourceTracer:
    """Get singleton instance of SourceTracer."""
    global _source_tracer
    if _source_tracer is None:
        _source_tracer = SourceTracer()
    return _source_tracer
