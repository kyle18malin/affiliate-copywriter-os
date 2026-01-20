"""
Affiliate Copywriter OS - RSS Feed Service
Handles fetching and parsing news from multiple sources
"""
import feedparser
import httpx
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.models import RSSFeed, NewsArticle


# Pre-configured RSS feeds for insurance/finance niches
DEFAULT_FEEDS = [
    # General News
    {"name": "Google News - Top Stories", "url": "https://news.google.com/rss", "category": "General"},
    {"name": "Reuters - Top News", "url": "https://feeds.reuters.com/reuters/topNews", "category": "General"},
    
    # Finance & Economy
    {"name": "CNBC - Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "category": "Finance"},
    {"name": "MarketWatch - Top Stories", "url": "https://feeds.marketwatch.com/marketwatch/topstories/", "category": "Finance"},
    {"name": "Bloomberg - Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "category": "Finance"},
    
    # Insurance Specific
    {"name": "Insurance Journal", "url": "https://www.insurancejournal.com/feed/", "category": "Insurance"},
    {"name": "PropertyCasualty360", "url": "https://www.propertycasualty360.com/feed/", "category": "Insurance"},
    
    # Real Estate / Mortgage (for Refi)
    {"name": "HousingWire", "url": "https://www.housingwire.com/feed/", "category": "Real Estate"},
    {"name": "Mortgage News Daily", "url": "https://www.mortgagenewsdaily.com/rss/", "category": "Mortgage"},
    
    # Consumer Finance
    {"name": "NerdWallet", "url": "https://www.nerdwallet.com/blog/feed/", "category": "Personal Finance"},
    {"name": "The Penny Hoarder", "url": "https://www.thepennyhoarder.com/feed/", "category": "Personal Finance"},
]


async def fetch_feed(url: str, timeout: float = 30.0) -> Optional[feedparser.FeedParserDict]:
    """Fetch and parse an RSS feed"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=timeout, follow_redirects=True)
            if response.status_code == 200:
                return feedparser.parse(response.text)
    except Exception as e:
        print(f"Error fetching feed {url}: {e}")
    return None


async def init_default_feeds(db: AsyncSession):
    """Initialize database with default RSS feeds"""
    for feed_data in DEFAULT_FEEDS:
        # Check if feed already exists
        result = await db.execute(
            select(RSSFeed).where(RSSFeed.url == feed_data["url"])
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            feed = RSSFeed(
                name=feed_data["name"],
                url=feed_data["url"],
                category=feed_data["category"],
                is_active=True
            )
            db.add(feed)
    
    await db.commit()


async def add_feed(db: AsyncSession, name: str, url: str, category: str = "General") -> RSSFeed:
    """Add a new RSS feed"""
    feed = RSSFeed(name=name, url=url, category=category, is_active=True)
    db.add(feed)
    await db.commit()
    await db.refresh(feed)
    return feed


async def get_all_feeds(db: AsyncSession) -> list[RSSFeed]:
    """Get all RSS feeds"""
    result = await db.execute(select(RSSFeed).order_by(RSSFeed.category, RSSFeed.name))
    return list(result.scalars().all())


async def fetch_all_news(db: AsyncSession) -> dict:
    """Fetch news from all active RSS feeds"""
    result = await db.execute(
        select(RSSFeed).where(RSSFeed.is_active == True)
    )
    feeds = result.scalars().all()
    
    stats = {"feeds_processed": 0, "articles_added": 0, "errors": []}
    
    for feed in feeds:
        parsed = await fetch_feed(feed.url)
        if not parsed or not parsed.entries:
            stats["errors"].append(f"Failed to fetch: {feed.name}")
            continue
        
        stats["feeds_processed"] += 1
        
        for entry in parsed.entries[:20]:  # Limit to 20 most recent per feed
            # Check if article already exists
            existing = await db.execute(
                select(NewsArticle).where(NewsArticle.url == entry.get("link", ""))
            )
            if existing.scalar_one_or_none():
                continue
            
            # Parse published date
            published = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                try:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                except:
                    pass
            
            article = NewsArticle(
                feed_id=feed.id,
                title=entry.get("title", "")[:500],
                summary=entry.get("summary", "")[:2000] if entry.get("summary") else None,
                url=entry.get("link", ""),
                published_at=published
            )
            db.add(article)
            stats["articles_added"] += 1
        
        # Update last fetched time
        feed.last_fetched = datetime.now(timezone.utc)
    
    await db.commit()
    return stats


async def get_recent_articles(db: AsyncSession, limit: int = 50, category: str = None) -> list[NewsArticle]:
    """Get recent news articles, optionally filtered by feed category"""
    query = select(NewsArticle).options(selectinload(NewsArticle.feed))
    
    if category:
        query = query.join(RSSFeed).where(RSSFeed.category == category)
    
    query = query.order_by(NewsArticle.fetched_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_trending_articles(db: AsyncSession, limit: int = 20) -> list[NewsArticle]:
    """Get articles with highest relevance scores (after AI analysis)"""
    result = await db.execute(
        select(NewsArticle)
        .where(NewsArticle.relevance_score.isnot(None))
        .order_by(NewsArticle.relevance_score.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
