"""
Source Tracer Service

Traces statistics to their original sources using multiple methods:
1. Within article content (AI extraction + URL parsing)
2. Web search for the statistic
3. Cross-article database search

Enhanced with:
- Smart chunking (focus on statistic context + references section)
- Multi-turn AI reasoning for verification
- Organization existence verification
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

VERIFICATION_PROMPT = """You previously identified the source as: {source_name}

Please verify this extraction by:
1. Double-checking the article text actually mentions this organization
2. Confirming the statistic is attributed to this source
3. Checking if there are other possible sources mentioned

Return JSON:
{{
  "verified": true/false,
  "confidence_adjustment": 0.1 or -0.2 (how much to adjust confidence),
  "alternative_source": "Other Organization" or null,
  "reasoning": "Brief explanation of your verification"
}}
"""

# Known credible organizations for verification
KNOWN_ORGANIZATIONS = {
    'government': [
        'cdc', 'fbi', 'epa', 'fda', 'nih', 'doj', 'dhs', 'nasa', 'noaa', 'usgs',
        'census bureau', 'bureau of labor statistics', 'department of', 'white house'
    ],
    'research': [
        'pew research', 'rand corporation', 'brookings', 'gallup', 'ipsos',
        'mckinsey', 'gartner', 'forrester', 'kaiser family foundation'
    ],
    'academic': [
        'harvard', 'stanford', 'mit', 'yale', 'oxford', 'cambridge', 'princeton',
        'university of', 'college of', 'johns hopkins'
    ],
    'international': [
        'who', 'unesco', 'world bank', 'imf', 'un ', 'united nations', 'world health',
        'european commission', 'oecd'
    ],
    'media': [
        'reuters', 'associated press', 'bloomberg', 'wall street journal',
        'new york times', 'washington post', 'bbc', 'npr'
    ],
}


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
        """Enhanced trace source within article content with smart chunking and verification."""
        try:
            # Step 1: Extract references section if it exists
            references = self._extract_references_section(article_content)

            # Step 2: Get smart context (statistic context + references)
            context = self._get_relevant_context(statistic_text, article_content, references)

            # Step 3: Multi-turn AI extraction with verification
            ai_result = self._ai_extract_source_with_reasoning(statistic_text, context, article_url)

            if not ai_result:
                return None

            # Step 4: Verify organization exists
            if ai_result.get('source_name'):
                org_verification = self._verify_organization_exists(ai_result['source_name'])

                # Adjust confidence based on org verification
                if org_verification.get('verified'):
                    ai_result['confidence'] = min(1.0, ai_result.get('confidence', 0.5) + 0.1)
                    ai_result['organization_verified'] = True
                    ai_result['organization_category'] = org_verification.get('category')
                else:
                    ai_result['confidence'] = max(0.0, ai_result.get('confidence', 0.5) - 0.15)
                    ai_result['organization_verified'] = False

            # Step 5: Find nearby URLs
            nearby_urls = self._extract_nearby_urls(statistic_text, article_content)

            # If AI didn't find a URL but we found nearby URLs, use the first one
            if not ai_result.get("source_url") and nearby_urls:
                ai_result["source_url"] = nearby_urls[0]
                ai_result["confidence"] = min(ai_result.get("confidence", 0.5), 0.65)

            return ai_result

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

    def _extract_references_section(self, article_content: str) -> Optional[str]:
        """
        Extract the references/sources section from the end of an article.

        Args:
            article_content: Full article text

        Returns:
            References section text or None if not found
        """
        try:
            # Look for common reference section patterns
            patterns = [
                r'(?:Sources?|References?|Citations?):?\s*\n(.*?)(?:\n\n|\Z)',
                r'(?:This article cites?:?)\s*\n(.*?)(?:\n\n|\Z)',
                r'(?:Read more:?|Learn more:?|Further reading:?)\s*\n(.*?)(?:\n\n|\Z)',
                r'(?:Based on data from:?)\s*\n(.*?)(?:\n\n|\Z)',
            ]

            for pattern in patterns:
                match = re.search(pattern, article_content, re.IGNORECASE | re.DOTALL)
                if match:
                    references = match.group(1).strip()
                    # Only return if it's not too long (likely a real references section)
                    if len(references) < 1000:
                        logger.debug(f"Found references section: {references[:100]}...")
                        return references

            return None

        except Exception as e:
            logger.error(f"Error extracting references section: {e}")
            return None

    def _get_relevant_context(
        self,
        statistic_text: str,
        article_content: str,
        references_section: Optional[str] = None,
        max_chars: int = 3000
    ) -> str:
        """
        Get the most relevant portion of article for source tracing.

        Strategy:
        1. If statistic found: take context around it
        2. If references section exists: append it
        3. Fallback: take beginning + end (where sources often are)

        Args:
            statistic_text: The statistic to trace
            article_content: Full article text
            references_section: Optional references section
            max_chars: Maximum characters to return

        Returns:
            Optimized context for AI analysis
        """
        try:
            stat_lower = statistic_text.lower()
            content_lower = article_content.lower()

            # Try to find the statistic in the article
            stat_position = content_lower.find(stat_lower)

            if stat_position == -1 and len(stat_lower) > 30:
                # Try partial match
                stat_position = content_lower.find(stat_lower[:30])

            context_parts = []

            if stat_position != -1:
                # Take 1500 chars before and after the statistic
                start = max(0, stat_position - 1500)
                end = min(len(article_content), stat_position + len(statistic_text) + 1500)
                context_parts.append(article_content[start:end])
                logger.debug(f"Using context around statistic position {stat_position}")
            else:
                # Fallback: take beginning + end
                if len(article_content) <= max_chars:
                    context_parts.append(article_content)
                else:
                    context_parts.append(article_content[:2000])
                    context_parts.append("\n\n[... article continues ...]\n\n")
                    context_parts.append(article_content[-1000:])
                logger.debug("Statistic not found, using beginning + end strategy")

            # Append references section if available
            if references_section:
                context_parts.append(f"\n\n--- REFERENCES SECTION ---\n{references_section}")

            combined = "".join(context_parts)

            # Truncate if still too long
            if len(combined) > max_chars:
                combined = combined[:max_chars] + "..."

            return combined

        except Exception as e:
            logger.error(f"Error getting relevant context: {e}")
            # Fallback to simple truncation
            return article_content[:max_chars] + "..."

    def _ai_extract_source_with_reasoning(
        self,
        statistic_text: str,
        article_content: str,
        article_url: str
    ) -> Optional[Dict]:
        """
        Multi-turn AI extraction with self-verification.

        Args:
            statistic_text: The statistic to trace
            article_content: Article context (pre-optimized)
            article_url: URL of the article

        Returns:
            Dict with source info and verification results
        """
        if not self.openai_api:
            logger.warning("OpenAI API key not configured - cannot extract source")
            return None

        try:
            # Turn 1: Initial extraction
            prompt = TRACE_SOURCE_PROMPT.format(
                article_url=article_url,
                statistic_text=statistic_text,
                article_content=article_content
            )

            messages = [
                {"role": "system", "content": "You are an expert at identifying sources and citations in articles."},
                {"role": "user", "content": prompt}
            ]

            response_1 = self.openai_api.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=300
            )

            content_1 = response_1.choices[0].message.content.strip()

            # Parse initial result
            if content_1.startswith("```"):
                content_1 = content_1.split("```")[1]
                if content_1.startswith("json"):
                    content_1 = content_1[4:]
            content_1 = content_1.strip()

            initial_result = json.loads(content_1)

            if not isinstance(initial_result, dict):
                logger.error(f"AI returned non-dict result: {initial_result}")
                return None

            # If no source name found, skip verification
            if not initial_result.get('source_name'):
                initial_result['confidence'] = initial_result.get('confidence', 0.0)
                return initial_result

            # Turn 2: Verification step
            messages.append({"role": "assistant", "content": content_1})

            verification_prompt = VERIFICATION_PROMPT.format(
                source_name=initial_result.get('source_name')
            )

            messages.append({"role": "user", "content": verification_prompt})

            response_2 = self.openai_api.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.3,
                max_tokens=200
            )

            content_2 = response_2.choices[0].message.content.strip()

            # Parse verification result
            if content_2.startswith("```"):
                content_2 = content_2.split("```")[1]
                if content_2.startswith("json"):
                    content_2 = content_2[4:]
            content_2 = content_2.strip()

            verification = json.loads(content_2)

            # Apply verification adjustments
            if verification.get('verified'):
                adjustment = verification.get('confidence_adjustment', 0.0)
                initial_result['confidence'] = min(1.0,
                    initial_result.get('confidence', 0.5) + adjustment)
                initial_result['ai_verified'] = True
            else:
                # If verification failed, check for alternative source
                if verification.get('alternative_source'):
                    initial_result['source_name'] = verification['alternative_source']
                    initial_result['confidence'] = 0.6
                else:
                    initial_result['confidence'] = max(0.0,
                        initial_result.get('confidence', 0.5) - 0.2)
                initial_result['ai_verified'] = False

            initial_result['verification_reasoning'] = verification.get('reasoning', '')

            logger.info(
                f"AI extracted and verified source: {initial_result.get('source_name', 'Unknown')} "
                f"(confidence: {initial_result.get('confidence', 0.0):.2f}, "
                f"verified: {initial_result.get('ai_verified', False)})"
            )

            return initial_result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            # Fallback to single-turn extraction
            return self._ai_extract_source(statistic_text, article_content, article_url)
        except Exception as e:
            logger.error(f"Error in multi-turn AI extraction: {e}")
            # Fallback to single-turn extraction
            return self._ai_extract_source(statistic_text, article_content, article_url)

    def _verify_organization_exists(self, source_name: str) -> Dict:
        """
        Verify organization exists using knowledge base and heuristics.

        Args:
            source_name: Organization name to verify

        Returns:
            Dict with verified status, category, confidence, method
        """
        try:
            name_lower = source_name.lower()

            # Check against known organizations
            for category, orgs in KNOWN_ORGANIZATIONS.items():
                for org in orgs:
                    if org in name_lower:
                        logger.debug(f"Organization '{source_name}' verified via knowledge base ({category})")
                        return {
                            'verified': True,
                            'category': category,
                            'confidence': 0.95,
                            'method': 'knowledge_base'
                        }

            # Check for credible suffixes/keywords
            credible_patterns = [
                (r'\.gov\b', 'government', 0.9),
                (r'\.edu\b', 'academic', 0.85),
                (r'\buniversity\b', 'academic', 0.8),
                (r'\binstitute\b', 'research', 0.75),
                (r'\bbureau\b', 'government', 0.75),
                (r'\bagency\b', 'government', 0.75),
                (r'\bfoundation\b', 'research', 0.7),
                (r'\bcenter\b', 'research', 0.65),
                (r'\bassociation\b', 'research', 0.65),
            ]

            for pattern, category, confidence in credible_patterns:
                if re.search(pattern, name_lower):
                    logger.debug(f"Organization '{source_name}' verified via pattern ({category})")
                    return {
                        'verified': True,
                        'category': category,
                        'confidence': confidence,
                        'method': 'heuristic'
                    }

            # If still not verified, try web search (optional, requires API key)
            if settings.google_fact_check_api_key and hasattr(settings, 'google_search_engine_id'):
                web_verification = self._verify_organization_via_web(source_name)
                if web_verification.get('verified'):
                    return web_verification

            # Organization not recognized
            logger.debug(f"Organization '{source_name}' not verified")
            return {
                'verified': False,
                'category': 'unknown',
                'confidence': 0.3,
                'method': 'unknown'
            }

        except Exception as e:
            logger.error(f"Error verifying organization: {e}")
            return {
                'verified': False,
                'confidence': 0.0,
                'method': 'error'
            }

    def _verify_organization_via_web(self, source_name: str) -> Dict:
        """
        Verify organization exists via Google search (optional fallback).

        Args:
            source_name: Organization name to verify

        Returns:
            Dict with verification results
        """
        try:
            search_query = f'"{source_name}" official website'

            response = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params={
                    "key": settings.google_fact_check_api_key,
                    "cx": settings.google_search_engine_id,
                    "q": search_query,
                    "num": 1
                },
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('items') and len(data['items']) > 0:
                    top_result = data['items'][0]
                    logger.debug(f"Organization '{source_name}' verified via web search")
                    return {
                        'verified': True,
                        'category': 'web_verified',
                        'confidence': 0.7,
                        'method': 'web_search',
                        'website': top_result.get('link'),
                        'snippet': top_result.get('snippet', '')[:200]
                    }

            return {'verified': False, 'confidence': 0.2, 'method': 'web_search_failed'}

        except Exception as e:
            logger.warning(f"Web verification error for '{source_name}': {e}")
            return {'verified': False, 'confidence': 0.0, 'method': 'web_search_error'}


# Singleton instance
_source_tracer = None


def get_source_tracer() -> SourceTracer:
    """Get singleton instance of SourceTracer."""
    global _source_tracer
    if _source_tracer is None:
        _source_tracer = SourceTracer()
    return _source_tracer
