"""
LLM-based Parser: Extract structured data from articles using Claude API
Extracts: company name, amount, round, investors, country, date
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import anthropic

logger = logging.getLogger(__name__)

CLAUDE_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = "claude-3-5-sonnet-20241022"  # Latest Claude model

# Extraction prompt
EXTRACTION_PROMPT = """
You are an expert at extracting funding information from news articles about startups.

Parse the following article and extract structured funding information.

Return ONLY valid JSON (no markdown, no explanations) with this exact structure:
{
    "company": "Company name or null",
    "amount": number (in USD, or null),
    "round": "Seed/Series A/Series B/Series C/other round type or null",
    "investors": ["Investor 1", "Investor 2"] (list of investor names or empty),
    "country": "Country name or null",
    "date": "YYYY-MM-DD or null"
}

Rules:
- Extract ONLY information explicitly stated in the article
- If information is not mentioned, use null
- Amount must be a number in USD (convert if needed, e.g., "$5M" = 5000000)
- Country: Use full country name
- Date: Extract announcement date in YYYY-MM-DD format
- Investors: List individual investors, VCs, or funds mentioned
- Return valid JSON only - no additional text

Article:
---
{article}
---

Return only JSON:
"""


class ClaudeParser:
    """Extract structured funding data using Claude API"""

    def __init__(self, api_key: str = CLAUDE_API_KEY, model: str = MODEL):
        self.api_key = api_key
        self.model = model
        self.client = anthropic.Anthropic(api_key=api_key) if api_key else None

    def parse_article(self, article_text: str, title: str = "") -> Optional[Dict[str, Any]]:
        """
        Parse a single article and extract funding information
        
        Args:
            article_text: Full article content
            title: Article title for context
            
        Returns:
            Extracted data as dict, or None if parsing fails
        """
        if not self.client:
            logger.warning("⚠️  Claude API key not set, skipping parsing")
            return None

        if not article_text or len(article_text.strip()) < 50:
            logger.debug("Article too short, skipping")
            return None

        try:
            # Build content to parse
            content_to_parse = f"Title: {title}\n\n{article_text}"

            # Call Claude API
            message = self.client.messages.create(
                model=self.model,
                max_tokens=1024,
                messages=[
                    {
                        "role": "user",
                        "content": EXTRACTION_PROMPT.format(article=content_to_parse),
                    }
                ],
            )

            # Extract response
            response_text = message.content[0].text.strip()

            # Parse JSON
            # Handle case where response might have markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()

            data = json.loads(response_text)

            # Validate extracted data
            if data.get("company"):
                logger.debug(f"✅ Parsed: {data.get('company')} - ${data.get('amount', 'unknown')} {data.get('round', '')}")
                return data
            else:
                logger.debug("No company found in article")
                return None

        except json.JSONDecodeError as e:
            logger.warning(f"⚠️  Failed to parse JSON response: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"❌ Claude parsing error: {str(e)}")
            return None

    def parse_batch(self, articles: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Parse multiple articles
        
        Args:
            articles: List of dicts with 'title', 'content', 'url', etc.
            
        Returns:
            List of extracted data dicts
        """
        extracted_data = []
        successful = 0
        failed = 0

        logger.info(f"🔄 Parsing {len(articles)} articles with Claude...")

        for i, article in enumerate(articles):
            logger.info(f"  Parsing article {i+1}/{len(articles)}: {article.get('title', 'No title')[:50]}")

            content = article.get("content", "") or article.get("summary", "")
            title = article.get("title", "")

            parsed = self.parse_article(content, title)

            if parsed:
                # Add metadata
                parsed["source_url"] = article.get("url", "")
                parsed["source"] = article.get("source", "unknown")
                extracted_data.append(parsed)
                successful += 1
            else:
                failed += 1

        logger.info(f"✅ Parsing complete: {successful} successful, {failed} failed")
        return extracted_data


def parse_articles_batch(articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Main function to parse articles"""
    parser = ClaudeParser()
    return parser.parse_batch(articles)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Test with sample article
    sample_article = """
    TechVision, an AI-powered analytics startup, announced today that it has raised $15 million 
    in Series A funding led by Sequoia Capital. The round also included participation from Y Combinator 
    and Google Ventures. The company plans to use the funding to expand its team and accelerate 
    product development. Founded in 2024 by former Google engineers, TechVision is headquartered 
    in San Francisco, USA.
    """

    parser = ClaudeParser()
    result = parser.parse_article(sample_article, "TechVision Raises $15M Series A")
    print(json.dumps(result, indent=2))
