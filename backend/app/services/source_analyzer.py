"""
Source Analyzer Service

Analyzes news sources to determine organizational bias using AI.
This service uses OpenAI to analyze the domain name, source name, and article content
to infer the organizational bias of user-submitted sources.

Also provides functionality to analyze and create sources from RSS feed URLs.
"""

import logging
import feedparser
from typing import Optional, Dict, Any, List
from urllib.parse import urlparse
from sqlmodel import Session, select

from ..models import Source, OrganizationalBias
from ..utils.openai_client import openai_client
from ..config import settings

logger = logging.getLogger(__name__)


class SourceAnalyzer:
    """Service for analyzing source organizational bias."""

    def __init__(self, db: Session):
        self.db = db

    def analyze_source_bias(
        self,
        source: Source,
        article_content: Optional[str] = None,
        article_title: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyze source organizational bias using AI.

        Args:
            source: Source object to analyze
            article_content: Optional article content for additional context
            article_title: Optional article title for additional context

        Returns:
            Dictionary with bias analysis results:
            {
                "organizational_bias": OrganizationalBias enum value,
                "bias_description": str,
                "confidence": float (0.0-1.0)
            }
            Returns None if analysis fails or AI is not available.
        """
        if not openai_client.is_available():
            logger.warning("OpenAI API not available, skipping source bias analysis")
            return None

        # Skip analysis if source already has bias set
        if source.organizational_bias:
            logger.info(f"Source {source.name} already has bias set to {source.organizational_bias.value}")
            return {
                "organizational_bias": source.organizational_bias,
                "bias_description": source.bias_description or "",
                "confidence": 1.0  # Existing data is trusted
            }

        try:
            # Prepare context for AI
            domain = urlparse(source.url).netloc

            # Build prompt
            prompt = self._build_bias_analysis_prompt(
                source_name=source.name,
                domain=domain,
                article_title=article_title,
                article_content=article_content
            )

            # Call OpenAI
            response = openai_client.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert media analyst who identifies organizational bias in news sources."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more consistent results
                response_format={"type": "json_object"}
            )

            # Parse response
            result = response.choices[0].message.content
            import json
            parsed_result = json.loads(result)

            # Map bias string to enum
            bias_str = parsed_result.get("bias", "center").lower()
            organizational_bias = self._map_bias_string_to_enum(bias_str)

            return {
                "organizational_bias": organizational_bias,
                "bias_description": parsed_result.get("description", ""),
                "confidence": parsed_result.get("confidence", 0.5)
            }

        except Exception as e:
            logger.error(f"Error analyzing source bias for {source.name}: {str(e)}", exc_info=True)
            return None

    def update_source_with_bias(
        self,
        source: Source,
        bias_analysis: Dict[str, Any]
    ) -> Source:
        """
        Update source with bias analysis results.

        Args:
            source: Source object to update
            bias_analysis: Dictionary with bias analysis results

        Returns:
            Updated Source object
        """
        source.organizational_bias = bias_analysis["organizational_bias"]
        source.bias_description = bias_analysis["bias_description"]

        self.db.add(source)
        self.db.commit()
        self.db.refresh(source)

        logger.info(
            f"Updated source {source.name} with bias: {source.organizational_bias.value}"
        )

        return source

    def _build_bias_analysis_prompt(
        self,
        source_name: str,
        domain: str,
        article_title: Optional[str] = None,
        article_content: Optional[str] = None
    ) -> str:
        """Build prompt for AI bias analysis."""
        prompt = f"""Analyze the organizational bias of this news source:

Source Name: {source_name}
Domain: {domain}
"""

        if article_title:
            prompt += f"Sample Article Title: {article_title}\n"

        if article_content:
            # Limit content to first 1000 characters to avoid token limits
            content_sample = article_content[:1000] + "..." if len(article_content) > 1000 else article_content
            prompt += f"\nSample Article Content:\n{content_sample}\n"

        prompt += """
Based on the source name, domain, and available article content, determine the organizational bias.

Organizational Bias Categories:
- **left**: Consistently advocates for progressive/left-leaning policies
- **center-left**: Generally left-leaning but maintains some balance
- **center**: Neutral, balanced reporting with minimal editorial slant
- **center-right**: Generally right-leaning but maintains some balance
- **right**: Consistently advocates for conservative/right-leaning policies

Respond in JSON format with:
{
  "bias": "left" | "center-left" | "center" | "center-right" | "right",
  "description": "Brief 1-2 sentence explanation of the bias assessment",
  "confidence": 0.0-1.0 (how confident you are in this assessment)
}

Guidelines:
- Consider the domain TLD (.gov, .edu, .org, .com)
- Consider known news organizations (e.g., BBC, CNN, Fox News, NPR)
- If unknown, use article content tone and framing as evidence
- Default to "center" if insufficient evidence (with low confidence)
- Be objective and base assessment on journalistic standards, not personal views
"""

        return prompt

    def _map_bias_string_to_enum(self, bias_str: str) -> OrganizationalBias:
        """Map bias string from AI to OrganizationalBias enum."""
        bias_mapping = {
            "left": OrganizationalBias.LEFT,
            "center-left": OrganizationalBias.CENTER_LEFT,
            "center": OrganizationalBias.CENTER,
            "center-right": OrganizationalBias.CENTER_RIGHT,
            "right": OrganizationalBias.RIGHT
        }

        return bias_mapping.get(bias_str.lower(), OrganizationalBias.CENTER)

    def analyze_rss_feed(self, rss_url: str) -> Dict[str, Any]:
        """
        Analyze a source by its RSS feed URL and generate complete metadata.

        Args:
            rss_url: RSS feed URL to analyze

        Returns:
            Dict containing:
                - name: Source name
                - url: Source website URL
                - description: AI-generated description
                - organizational_bias: Political lean (OrganizationalBias enum)
                - bias_description: Explanation of bias
                - trust_score: Credibility rating (0.0-1.0)

        Raises:
            ValueError: If RSS feed cannot be fetched or parsed
        """
        logger.info(f"Analyzing source from RSS URL: {rss_url}")

        # Step 1: Fetch RSS feed
        feed_data = self._fetch_feed(rss_url)

        # Step 2: Extract basic metadata
        metadata = self._extract_feed_metadata(feed_data)

        # Step 3: Sample recent articles
        article_samples = self._sample_feed_articles(feed_data, max_articles=5)

        # Step 4: Generate AI analysis
        ai_analysis = self._generate_comprehensive_analysis(metadata, article_samples)

        # Combine results
        result = {
            "name": metadata["name"],
            "url": metadata["url"],
            "rss_feed_url": rss_url,
            "description": ai_analysis["description"],
            "organizational_bias": ai_analysis["organizational_bias"],
            "bias_description": ai_analysis["bias_description"],
            "trust_score": ai_analysis["trust_score"],
        }

        logger.info(f"Source analysis complete: {result['name']}")
        return result

    def _fetch_feed(self, rss_url: str) -> feedparser.FeedParserDict:
        """
        Fetch and parse RSS feed.

        Args:
            rss_url: RSS feed URL

        Returns:
            Parsed feed data

        Raises:
            ValueError: If feed cannot be fetched or parsed
        """
        try:
            feed = feedparser.parse(rss_url)

            if feed.bozo and not feed.entries:
                logger.error(f"RSS feed has critical parsing errors: {rss_url}")
                raise ValueError("RSS feed has critical parsing errors")

            if not feed.entries:
                raise ValueError("RSS feed contains no entries")

            return feed

        except Exception as e:
            logger.error(f"Error fetching RSS feed {rss_url}: {str(e)}")
            raise ValueError(f"Failed to fetch RSS feed: {str(e)}")

    def _extract_feed_metadata(self, feed: feedparser.FeedParserDict) -> Dict[str, str]:
        """
        Extract basic metadata from RSS feed.

        Args:
            feed: Parsed feed data

        Returns:
            Dict with name and url
        """
        feed_info = feed.get("feed", {})

        # Extract source name (prefer title, fallback to link domain)
        name = feed_info.get("title", "Unknown Source")

        # Extract source URL (prefer link, fallback to entries)
        url = feed_info.get("link", "")
        if not url and feed.entries:
            # Try to extract domain from first entry link
            first_entry_link = feed.entries[0].get("link", "")
            if first_entry_link:
                parsed = urlparse(first_entry_link)
                url = f"{parsed.scheme}://{parsed.netloc}"

        return {
            "name": name,
            "url": url
        }

    def _sample_feed_articles(self, feed: feedparser.FeedParserDict, max_articles: int = 5) -> List[Dict]:
        """
        Sample recent articles from feed for analysis.

        Args:
            feed: Parsed feed data
            max_articles: Maximum number of articles to sample

        Returns:
            List of article samples with title and summary
        """
        samples = []

        for entry in feed.entries[:max_articles]:
            title = entry.get("title", "")
            summary = entry.get("summary", "") or entry.get("description", "")

            # Clean HTML tags from summary
            import re
            summary = re.sub(r'<[^>]+>', '', summary)

            samples.append({
                "title": title,
                "summary": summary[:300]  # Limit summary length
            })

        return samples

    def _generate_comprehensive_analysis(self, metadata: Dict, article_samples: List[Dict]) -> Dict[str, Any]:
        """
        Use AI to analyze source characteristics comprehensively.

        Args:
            metadata: Basic source metadata (name, url)
            article_samples: Sample articles for analysis

        Returns:
            Dict with AI-generated analysis:
                - description: Source description
                - organizational_bias: Political lean (OrganizationalBias enum)
                - bias_description: Explanation of bias
                - trust_score: Credibility rating
        """
        if not openai_client.is_available():
            logger.warning("OpenAI API not available, using defaults")
            return self._get_default_analysis(metadata)

        # Build prompt with metadata and samples
        articles_text = "\n".join([
            f"- {sample['title']}\n  {sample['summary']}"
            for sample in article_samples
        ])

        prompt = f"""Analyze this news source and provide comprehensive information:

Source Name: {metadata['name']}
Source URL: {metadata['url']}

Recent Articles:
{articles_text}

Please provide:
1. A concise description (1-2 sentences) of this news source, highlighting its focus, reputation, and editorial stance.
2. The organizational bias on a political spectrum: "left", "center-left", "center", "center-right", or "right"
3. A brief explanation (1 sentence) of why this bias rating was assigned
4. A trust score from 0.0 to 1.0, where 1.0 is highly credible and 0.0 is not credible (based on journalistic standards, fact-checking record, and reputation)

Format your response as JSON:
{{
    "description": "source description here",
    "organizational_bias": "center",
    "bias_description": "explanation here",
    "trust_score": 0.85
}}
"""

        try:
            response = openai_client.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a media analyst specializing in news source credibility and bias assessment. Provide objective, evidence-based analysis."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            import json
            result = json.loads(response.choices[0].message.content)

            # Map bias string to enum
            bias_str = result.get("organizational_bias", "center")
            organizational_bias = self._map_bias_string_to_enum(bias_str)

            # Validate trust score
            trust_score = float(result.get("trust_score", 0.8))
            trust_score = max(0.0, min(1.0, trust_score))  # Clamp to [0, 1]

            return {
                "description": result.get("description", f"News source: {metadata['name']}"),
                "organizational_bias": organizational_bias,
                "bias_description": result.get("bias_description", ""),
                "trust_score": trust_score
            }

        except Exception as e:
            logger.error(f"Error generating comprehensive AI analysis: {str(e)}")
            return self._get_default_analysis(metadata)

    def _get_default_analysis(self, metadata: Dict) -> Dict[str, Any]:
        """Return default analysis when AI is unavailable."""
        return {
            "description": f"News source providing coverage from {metadata['name']}",
            "organizational_bias": OrganizationalBias.CENTER,
            "bias_description": "Unable to determine bias",
            "trust_score": 0.7
        }