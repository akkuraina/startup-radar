"""
Data Fetcher: Tavily API + RSS Feeds
Collects raw funding articles and data
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
import requests
import feedparser
from urllib.parse import quote

logger = logging.getLogger(__name__)

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
TAVILY_BASE_URL = "https://api.tavily.com/search"

# RSS feeds for startup funding news
RSS_FEEDS = [
    "https://feeds.techcrunch.com/techcrunch/",  # TechCrunch
    "https://feeds.bloomberg.com/markets/news.rss",  # Bloomberg
    "https://feeds.cnbc.com/cnbc/news",  # CNBC
    "https://feeds.reuters.com/reuters/businessNews",  # Reuters
]

# Search queries to find funding announcements
FUNDING_QUERIES = [
    "Series A funding",
    "Series B funding",
    "Seed funding",
    "raised funding",
    "funding announcement",
    "venture capital",
    "startup investment",
]


class TavilyFetcher:
    """Fetch articles from Tavily API"""

    def __init__(self, api_key: str = TAVILY_API_KEY):
        self.api_key = api_key
        self.base_url = TAVILY_BASE_URL

    def search(self, query: str, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Search Tavily API for funding-related articles
        
        Args:
            query: Search query
            days_back: How many days back to search
            
        Returns:
            List of articles with title, content, url, published_date
        """
        if not self.api_key:
            logger.warning("⚠️  Tavily API key not set, skipping Tavily fetch")
            return []

        try:
            # Build date range for search
            start_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            payload = {
                "api_key": self.api_key,
                "query": query,
                "topic": "news",
                "days": days_back,
                "max_results": 10,  # Tavily limit
                "include_answer": False,
                "include_raw_content": True,
            }

            response = requests.post(self.base_url, json=payload, timeout=15)
            response.raise_for_status()

            data = response.json()
            articles = []

            if "results" in data:
                for result in data["results"]:
                    articles.append({
                        "title": result.get("title", ""),
                        "content": result.get("content", ""),
                        "url": result.get("url", ""),
                        "published_date": result.get("published_date"),
                        "source": "tavily",
                    })

            logger.info(f"✅ Tavily: Found {len(articles)} articles for '{query}'")
            return articles

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Tavily API error: {str(e)}")
            return []
        except Exception as e:
            logger.error(f"❌ Tavily fetch error: {str(e)}")
            return []

    def fetch_all(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """Fetch articles for all funding queries"""
        all_articles = []

        for query in FUNDING_QUERIES:
            articles = self.search(query, days_back)
            all_articles.extend(articles)

        # Remove duplicates by URL
        seen_urls = set()
        unique_articles = []
        for article in all_articles:
            url = article.get("url", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_articles.append(article)

        logger.info(f"📊 Tavily: Total unique articles after dedup: {len(unique_articles)}")
        return unique_articles


class RSSFetcher:
    """Fetch articles from RSS feeds"""

    def __init__(self, feeds: List[str] = None):
        self.feeds = feeds or RSS_FEEDS

    def fetch_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """
        Fetch articles from a single RSS feed
        
        Args:
            feed_url: URL of RSS feed
            
        Returns:
            List of articles
        """
        try:
            feed = feedparser.parse(feed_url)
            articles = []

            for entry in feed.entries[:20]:  # Limit to last 20 entries
                # Try to extract published date
                pub_date = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    pub_date = datetime(*entry.published_parsed[:6]).isoformat()

                article = {
                    "title": entry.get("title", ""),
                    "content": entry.get("summary", ""),
                    "url": entry.get("link", ""),
                    "published_date": pub_date,
                    "source": f"rss_{feed.feed.get('title', 'unknown')}",
                }
                
                # Only include if content looks relevant to funding
                text_to_check = f"{article['title']} {article['content']}".lower()
                if any(keyword in text_to_check for keyword in ["fund", "invest", "raise", "series", "seed"]):
                    articles.append(article)

            logger.info(f"✅ RSS: Found {len(articles)} relevant articles from {feed.feed.get('title', 'Unknown')}")
            return articles

        except Exception as e:
            logger.warning(f"⚠️  Failed to fetch RSS feed {feed_url}: {str(e)}")
            return []

    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch articles from all RSS feeds"""
        all_articles = []

        for feed_url in self.feeds:
            articles = self.fetch_feed(feed_url)
            all_articles.extend(articles)

        logger.info(f"📊 RSS: Total articles from all feeds: {len(all_articles)}")
        return all_articles


def fetch_all_sources(days_back: int = 7) -> List[Dict[str, Any]]:
    """
    Fetch from all sources: Tavily + RSS
    
    Args:
        days_back: How many days back to search
        
    Returns:
        Combined list of articles
    """
    logger.info(f"🔍 Starting data fetch (last {days_back} days)...")
    
    all_articles = []

    # Fetch from Tavily
    tavily = TavilyFetcher()
    tavily_articles = tavily.fetch_all(days_back=days_back)
    all_articles.extend(tavily_articles)

    # Fetch from RSS
    rss = RSSFetcher()
    rss_articles = rss.fetch_all()
    all_articles.extend(rss_articles)

    # Remove duplicates by URL
    seen_urls = set()
    unique_articles = []
    for article in all_articles:
        url = article.get("url", "")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_articles.append(article)

    logger.info(f"✅ Total unique articles collected: {len(unique_articles)}")
    return unique_articles


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    articles = fetch_all_sources(days_back=7)
    print(f"\nFetched {len(articles)} articles")
    if articles:
        print(f"\nFirst article sample:")
        print(articles[0])
