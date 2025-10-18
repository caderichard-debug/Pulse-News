"""
Source Analyzer Service

Analyzes news sources to determine organizational bias using AI.
This service uses OpenAI to analyze the domain name, source name, and article content
to infer the organizational bias of user-submitted sources.
"""

import logging
from typing import Optional, Dict, Any
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