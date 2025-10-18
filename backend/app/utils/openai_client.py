"""
OpenAI API client wrapper for article analysis.
Handles batch processing, cost tracking, and error handling.

To use this:
1. Get an API key from https://platform.openai.com/api-keys
2. Set OPENAI_API_KEY in your .env file
3. The default model is gpt-4o-mini (cheapest GPT-4 option)
"""

from openai import OpenAI
from ..config import settings
import logging
import json
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class OpenAIClient:
    """Wrapper for OpenAI API with batch processing support"""

    def __init__(self):
        if not settings.openai_api_key:
            logger.warning("OPENAI_API_KEY not set - AI features will be disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=settings.openai_api_key)
            logger.info(f"OpenAI client initialized with model: {settings.ai_model}")

    def is_available(self) -> bool:
        """Check if OpenAI API is configured and available"""
        return self.client is not None

    def analyze_articles_batch(
        self,
        articles: List[Dict[str, str]],
        max_tokens: int = 2000
    ) -> Optional[List[Dict]]:
        """
        Analyze a batch of articles (up to 5 recommended) in one API call.

        Args:
            articles: List of dicts with 'title' and 'content' keys
            max_tokens: Maximum tokens for response

        Returns:
            List of analysis results, one per article, or None if API unavailable
        """
        if not self.is_available():
            logger.error("OpenAI API not available - check OPENAI_API_KEY")
            return None

        if not articles:
            return []

        # Build prompt for batch analysis
        prompt = self._build_batch_analysis_prompt(articles)

        try:
            logger.info(f"Sending {len(articles)} articles to OpenAI for analysis...")

            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a news analysis assistant that provides objective analysis of articles including summaries, sentiment, political lean, and bias detection."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,  # Lower temperature for more consistent analysis
                response_format={"type": "json_object"}  # Ensure JSON response
            )

            # Extract and parse the response
            response_text = response.choices[0].message.content

            # Parse JSON response - OpenAI wraps in {"analyses": [...]}
            response_data = json.loads(response_text)
            analyses = response_data.get("analyses", response_data)

            # Log token usage for cost tracking
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self._calculate_cost(input_tokens, output_tokens)

            logger.info(
                f"Analysis complete: {input_tokens} input + {output_tokens} output tokens"
                f" = ${cost:.4f}"
            )

            return analyses

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse OpenAI response as JSON: {e}")
            logger.error(f"Response text: {response_text[:500]}")
            return None
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}", exc_info=True)
            return None

    def generate_frameworks(
        self,
        article_summaries: List[str],
        existing_frameworks: List[str],
        max_tokens: int = 1500
    ) -> Optional[List[Dict]]:
        """
        Generate new ethical/moral frameworks based on recent articles.

        Args:
            article_summaries: List of article summaries to analyze
            existing_frameworks: Names of frameworks we already have
            max_tokens: Maximum tokens for response

        Returns:
            List of new framework dicts or None if API unavailable
        """
        if not self.is_available():
            logger.error("OpenAI API not available - check OPENAI_API_KEY")
            return None

        prompt = self._build_framework_discovery_prompt(article_summaries, existing_frameworks)

        try:
            logger.info("Asking OpenAI to discover new ethical frameworks...")

            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in political philosophy and ethics who identifies underlying moral debates in current events."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.5,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            response_data = json.loads(response_text)
            frameworks = response_data.get("frameworks", response_data)

            logger.info(f"Generated {len(frameworks)} new framework suggestions")
            return frameworks

        except Exception as e:
            logger.error(f"Error generating frameworks: {e}", exc_info=True)
            return None

    def map_article_to_frameworks(
        self,
        article_title: str,
        article_summary: str,
        frameworks: List[Dict[str, str]],
        max_tokens: int = 1000
    ) -> Optional[List[Dict]]:
        """
        Map a single article to relevant frameworks.

        Args:
            article_title: Article title
            article_summary: Article summary
            frameworks: List of framework dicts with id, name, description, axis_description
            max_tokens: Maximum tokens for response

        Returns:
            List of mappings with framework_id, relevance_score, position_on_axis, explanation
        """
        if not self.is_available():
            return None

        prompt = self._build_framework_mapping_prompt(article_title, article_summary, frameworks)

        try:
            response = self.client.chat.completions.create(
                model=settings.ai_model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at mapping news articles to underlying ethical and moral debates."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=max_tokens,
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            response_text = response.choices[0].message.content
            response_data = json.loads(response_text)
            mappings = response_data.get("mappings", response_data)

            return mappings

        except Exception as e:
            logger.error(f"Error mapping article to frameworks: {e}", exc_info=True)
            return None

    def _build_batch_analysis_prompt(self, articles: List[Dict[str, str]]) -> str:
        """Build prompt for batch article analysis"""

        articles_text = ""
        for i, article in enumerate(articles, 1):
            articles_text += f"\n\n--- Article {i} ---\n"
            articles_text += f"Title: {article['title']}\n\n"
            articles_text += f"Content: {article['content'][:2000]}...\n"

        prompt = f"""Analyze the following news articles and provide objective analysis for each.

{articles_text}

For each article, provide:
1. **Summary**: A concise 100-word summary of the main points
2. **Sentiment**: An integer from -10 (very negative) to +10 (very positive)
3. **Political Lean**: One of: "left", "center", or "right" (lowercase)
4. **Bias Indicators**: Brief description of any detected bias (or "neutral" if none)
5. **Key Statistics**: Any important numbers, percentages, or data points mentioned
6. **Topic Category**: Classify into ONE of these categories (lowercase):
   - general: General news and current events
   - politics: Political news and policy
   - economics: Business, finance, and economic policy
   - technology: Tech industry, innovation, and digital culture
   - science: Scientific research and discoveries
   - culture: Arts, society, and cultural trends
   - world: International news and global affairs
   - environment: Climate, sustainability, and environmental issues

Return your analysis as a JSON object with this structure:

{{
  "analyses": [
    {{
      "summary": "100-word summary here",
      "sentiment_score": 0,
      "political_lean": "center",
      "bias_indicators": "Brief description or 'neutral'",
      "key_stats": ["stat 1", "stat 2"],
      "topic_category": "general"
    }},
    ...
  ]
}}

Provide one analysis object per article, in the same order."""

        return prompt

    def _build_framework_mapping_prompt(
        self,
        article_title: str,
        article_summary: str,
        frameworks: List[Dict[str, str]]
    ) -> str:
        """Build prompt for mapping article to frameworks"""

        frameworks_text = ""
        for fw in frameworks:
            frameworks_text += f"\n{fw['id']}. {fw['name']}\n"
            frameworks_text += f"   Description: {fw['description']}\n"
            frameworks_text += f"   Axis: {fw['axis_description']}\n"
            frameworks_text += f"   Left position: {fw['left_position']}\n"
            frameworks_text += f"   Right position: {fw['right_position']}\n"

        prompt = f"""Article to analyze:
Title: {article_title}
Summary: {article_summary}

Available ethical/moral frameworks:
{frameworks_text}

Which of these frameworks does this article relate to? For each relevant framework:
- Provide a relevance score (0.0 to 1.0, where 1.0 is highly relevant)
- Determine the article's position on the axis (-10 to +10, where -10 is far left position and +10 is far right position)
- Explain briefly how the article relates to this framework

Only include frameworks with relevance >= 0.3.

Return as JSON:
{{
  "mappings": [
    {{
      "framework_id": 1,
      "relevance_score": 0.8,
      "position_on_axis": -3,
      "explanation": "Brief explanation"
    }},
    ...
  ]
}}"""

        return prompt

    def _build_framework_discovery_prompt(
        self,
        article_summaries: List[str],
        existing_names: List[str]
    ) -> str:
        """Build prompt for discovering new frameworks"""

        summaries_text = "\n\n".join([f"- {s}" for s in article_summaries[:50]])
        existing_text = "\n".join([f"- {name}" for name in existing_names])

        prompt = f"""Based on these recent news article summaries, identify 1-3 NEW ethical or moral debates
that are NOT already covered by our existing frameworks.

Recent articles:
{summaries_text}

Existing frameworks (DO NOT suggest these):
{existing_text}

For each new framework, provide:
1. **Name**: Short, clear name (e.g., "Privacy vs. Security")
2. **Description**: 1-2 sentence explanation of the debate
3. **Axis Description**: How to think about the spectrum (e.g., "Level of government surveillance")
4. **Left Position**: What the left/progressive position represents (max 30 words)
5. **Right Position**: What the right/conservative position represents (max 30 words)

Focus on timeless ethical debates, not temporary political issues.

Return as JSON:
{{
  "frameworks": [
    {{
      "name": "Framework name",
      "description": "Description of the debate",
      "axis_description": "What the axis represents",
      "left_position": "Left/progressive stance",
      "right_position": "Right/conservative stance"
    }},
    ...
  ]
}}"""

        return prompt

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate API cost based on token usage.
        GPT-4o-mini pricing (as of 2024):
        - Input: $0.15 per 1M tokens
        - Output: $0.60 per 1M tokens
        """
        input_cost = (input_tokens / 1_000_000) * 0.15
        output_cost = (output_tokens / 1_000_000) * 0.60
        return input_cost + output_cost


# Global client instance
openai_client = OpenAIClient()
