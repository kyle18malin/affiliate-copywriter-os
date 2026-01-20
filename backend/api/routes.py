"""
Affiliate Copywriter OS - API Routes
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.services import rss_service, ad_service, ai_service, niche_service
from backend.models import GeneratedHook

router = APIRouter()


# ============== Pydantic Models ==============

class FeedCreate(BaseModel):
    name: str
    url: str
    category: str = "General"


class FeedResponse(BaseModel):
    id: int
    name: str
    url: str
    category: Optional[str]
    is_active: bool
    
    class Config:
        from_attributes = True


class AdCreate(BaseModel):
    content: str
    title: Optional[str] = None
    niche_id: Optional[int] = None
    source: Optional[str] = None
    performance_notes: Optional[str] = None


class AdResponse(BaseModel):
    id: int
    title: Optional[str]
    content: str
    niche_id: Optional[int]
    niche_name: Optional[str] = None
    source: Optional[str]
    performance_notes: Optional[str]
    patterns: Optional[dict] = None
    
    class Config:
        from_attributes = True


class NicheCreate(BaseModel):
    name: str
    description: Optional[str] = None


class NicheResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    
    class Config:
        from_attributes = True


class HookGenerateRequest(BaseModel):
    niche_id: int
    num_hooks: int = 5
    hook_style: Optional[str] = None  # e.g., "question", "story", "shocking stat"


class FullAdRequest(BaseModel):
    niche_id: int
    hook: str
    ad_format: str = "native"  # native, direct, story, listicle


class ArticleResponse(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    url: str
    feed_name: Optional[str] = None
    trending_angles: Optional[list] = None
    
    class Config:
        from_attributes = True


# ============== Niche Routes ==============

@router.get("/niches", response_model=list[NicheResponse])
async def get_niches(db: AsyncSession = Depends(get_db)):
    """Get all niches"""
    niches = await niche_service.get_all_niches(db)
    return niches


@router.post("/niches", response_model=NicheResponse)
async def create_niche(niche: NicheCreate, db: AsyncSession = Depends(get_db)):
    """Create a new niche"""
    return await niche_service.create_niche(db, niche.name, niche.description)


# ============== RSS Feed Routes ==============

@router.get("/feeds", response_model=list[FeedResponse])
async def get_feeds(db: AsyncSession = Depends(get_db)):
    """Get all RSS feeds"""
    feeds = await rss_service.get_all_feeds(db)
    return feeds


@router.post("/feeds", response_model=FeedResponse)
async def add_feed(feed: FeedCreate, db: AsyncSession = Depends(get_db)):
    """Add a new RSS feed"""
    return await rss_service.add_feed(db, feed.name, feed.url, feed.category)


@router.post("/feeds/fetch")
async def fetch_news(db: AsyncSession = Depends(get_db)):
    """Fetch news from all active RSS feeds"""
    stats = await rss_service.fetch_all_news(db)
    return stats


@router.get("/news")
async def get_news(
    limit: int = 50,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Get recent news articles"""
    articles = await rss_service.get_recent_articles(db, limit, category)
    return [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "url": a.url,
            "feed_name": a.feed.name if a.feed else None,
            "trending_angles": a.trending_angles,
            "published_at": a.published_at.isoformat() if a.published_at else None
        }
        for a in articles
    ]


@router.post("/news/{article_id}/analyze")
async def analyze_article(article_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze a news article for ad angles"""
    from sqlalchemy import select
    from backend.models import NewsArticle
    
    result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
    article = result.scalar_one_or_none()
    
    if not article:
        raise HTTPException(status_code=404, detail="Article not found")
    
    analysis = await ai_service.analyze_news_article(article.title, article.summary or "")
    
    # Save analysis to article
    article.trending_angles = analysis.get("trending_angles")
    article.emotional_triggers = analysis.get("emotional_triggers")
    article.relevance_score = analysis.get("relevance_score")
    
    await db.commit()
    
    return analysis


# ============== Ad Routes ==============

@router.get("/ads")
async def get_ads(niche_id: Optional[int] = None, db: AsyncSession = Depends(get_db)):
    """Get all ads, optionally filtered by niche"""
    ads = await ad_service.get_all_ads(db, niche_id)
    return [
        {
            "id": a.id,
            "title": a.title,
            "content": a.content,
            "niche_id": a.niche_id,
            "niche_name": a.niche.name if a.niche else None,
            "source": a.source,
            "performance_notes": a.performance_notes,
            "patterns": a.patterns[0].__dict__ if a.patterns else None,
            "created_at": a.created_at.isoformat() if a.created_at else None
        }
        for a in ads
    ]


@router.post("/ads")
async def create_ad(ad: AdCreate, db: AsyncSession = Depends(get_db)):
    """Upload a new winning ad"""
    new_ad = await ad_service.create_ad(
        db,
        content=ad.content,
        title=ad.title,
        niche_id=ad.niche_id,
        source=ad.source,
        performance_notes=ad.performance_notes
    )
    return {"id": new_ad.id, "message": "Ad created successfully"}


@router.post("/ads/{ad_id}/analyze")
async def analyze_ad(ad_id: int, db: AsyncSession = Depends(get_db)):
    """Analyze an ad and extract universal patterns"""
    ad = await ad_service.get_ad_by_id(db, ad_id)
    
    if not ad:
        raise HTTPException(status_code=404, detail="Ad not found")
    
    # Get AI analysis
    patterns = await ai_service.analyze_ad(ad.content)
    
    # Save patterns
    saved_pattern = await ad_service.save_ad_patterns(db, ad_id, patterns)
    
    return patterns


# ============== Hook Generation Routes ==============

@router.post("/generate/hooks")
async def generate_hooks(request: HookGenerateRequest, db: AsyncSession = Depends(get_db)):
    """Generate hooks for a specific niche"""
    # Get niche
    niche = await niche_service.get_niche_by_id(db, request.niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    # Get pattern summary (prioritizes niche-specific patterns)
    pattern_summary = await ad_service.get_pattern_summary(db, request.niche_id)
    
    # Get recent analyzed news
    articles = await rss_service.get_recent_articles(db, limit=10)
    recent_news = [
        {
            "title": a.title,
            "trending_angles": a.trending_angles or []
        }
        for a in articles if a.trending_angles
    ]
    
    # Generate hooks
    hooks = await ai_service.generate_hooks(
        niche=niche.name,
        pattern_summary=pattern_summary,
        recent_news=recent_news,
        num_hooks=request.num_hooks,
        hook_style=request.hook_style
    )
    
    # Save generated hooks to database
    from backend.models import GeneratedHook
    for hook_data in hooks:
        hook = GeneratedHook(
            niche_id=request.niche_id,
            hook_text=hook_data.get("hook_text", ""),
            hook_type=hook_data.get("hook_type"),
            news_angle=hook_data.get("inspiration")
        )
        db.add(hook)
    await db.commit()
    
    return {"hooks": hooks, "niche": niche.name}


@router.post("/generate/full-ad")
async def generate_full_ad(request: FullAdRequest, db: AsyncSession = Depends(get_db)):
    """Generate a full ad from a hook"""
    niche = await niche_service.get_niche_by_id(db, request.niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    pattern_summary = await ad_service.get_pattern_summary(db, request.niche_id)
    
    full_ad = await ai_service.generate_full_ad(
        niche=niche.name,
        hook=request.hook,
        pattern_summary=pattern_summary,
        ad_format=request.ad_format
    )
    
    return {"ad_copy": full_ad, "hook": request.hook, "format": request.ad_format}


@router.get("/hooks")
async def get_saved_hooks(
    niche_id: Optional[int] = None,
    favorites_only: bool = False,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """Get saved generated hooks"""
    from sqlalchemy import select
    from backend.models import GeneratedHook
    
    query = select(GeneratedHook)
    
    if niche_id:
        query = query.where(GeneratedHook.niche_id == niche_id)
    if favorites_only:
        query = query.where(GeneratedHook.is_favorite == True)
    
    query = query.order_by(GeneratedHook.created_at.desc()).limit(limit)
    result = await db.execute(query)
    hooks = result.scalars().all()
    
    return [
        {
            "id": h.id,
            "hook_text": h.hook_text,
            "hook_type": h.hook_type,
            "niche_id": h.niche_id,
            "is_favorite": h.is_favorite,
            "rating": h.rating,
            "created_at": h.created_at.isoformat() if h.created_at else None
        }
        for h in hooks
    ]


@router.patch("/hooks/{hook_id}/favorite")
async def toggle_favorite(hook_id: int, db: AsyncSession = Depends(get_db)):
    """Toggle favorite status of a hook"""
    from sqlalchemy import select
    from backend.models import GeneratedHook
    
    result = await db.execute(select(GeneratedHook).where(GeneratedHook.id == hook_id))
    hook = result.scalar_one_or_none()
    
    if not hook:
        raise HTTPException(status_code=404, detail="Hook not found")
    
    hook.is_favorite = not hook.is_favorite
    await db.commit()
    
    return {"id": hook_id, "is_favorite": hook.is_favorite}


# ============== Stats Route ==============

@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):
    """Get dashboard statistics"""
    from sqlalchemy import select, func
    from backend.models import RSSFeed, NewsArticle, Ad, AdPattern, GeneratedHook, Niche
    
    feeds_count = await db.execute(select(func.count(RSSFeed.id)))
    articles_count = await db.execute(select(func.count(NewsArticle.id)))
    ads_count = await db.execute(select(func.count(Ad.id)))
    patterns_count = await db.execute(select(func.count(AdPattern.id)))
    hooks_count = await db.execute(select(func.count(GeneratedHook.id)))
    
    return {
        "feeds": feeds_count.scalar(),
        "articles": articles_count.scalar(),
        "ads": ads_count.scalar(),
        "patterns": patterns_count.scalar(),
        "hooks_generated": hooks_count.scalar()
    }
