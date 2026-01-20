"""
Affiliate Copywriter OS - API Routes
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional
from backend.database import get_db
from backend.services import rss_service, ad_service, ai_service, niche_service
from backend.services import transcription_service, chat_service
from backend.models import GeneratedHook

router = APIRouter()

# Max file size: 25MB (Whisper API limit)
MAX_FILE_SIZE = 25 * 1024 * 1024

# In-memory conversation storage (per session)
# In production, you'd want to persist this to database
conversations = {}


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


class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    niche_id: Optional[int] = None
    # References to include in context
    ad_ids: Optional[list[int]] = None  # Reference specific winning ads
    article_ids: Optional[list[int]] = None  # Reference specific news articles


class ScriptRequest(BaseModel):
    script_type: str  # vsl, ugc, native, hooks, email
    niche_id: int
    topic: str
    additional_instructions: Optional[str] = None
    # References to include in context
    ad_ids: Optional[list[int]] = None
    article_ids: Optional[list[int]] = None


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


@router.delete("/niches/{niche_id}")
async def delete_niche(niche_id: int, db: AsyncSession = Depends(get_db)):
    """Delete a niche"""
    from sqlalchemy import select, update
    from backend.models import Niche, Ad
    
    # First unassign any ads from this niche
    await db.execute(
        update(Ad).where(Ad.niche_id == niche_id).values(niche_id=None)
    )
    
    # Delete the niche
    result = await db.execute(select(Niche).where(Niche.id == niche_id))
    niche = result.scalar_one_or_none()
    
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    await db.delete(niche)
    await db.commit()
    
    return {"message": "Niche deleted successfully"}


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


@router.get("/news/scored")
async def get_scored_news(
    limit: int = 100,
    min_score: int = 0,
    db: AsyncSession = Depends(get_db)
):
    """
    Get news articles scored and sorted by copywriting potential.
    Uses quick keyword-based scoring for speed.
    """
    from backend.services import news_scoring_service
    
    articles = await rss_service.get_recent_articles(db, limit)
    
    # Convert to dicts for scoring
    article_dicts = [
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
    
    # Score articles
    scored = await news_scoring_service.batch_score_articles(article_dicts, use_ai=False)
    
    # Filter by minimum score
    if min_score > 0:
        scored = [a for a in scored if a.get("relevance_score", 0) >= min_score]
    
    return scored


@router.get("/news/grouped")
async def get_grouped_news(
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Get news articles grouped by category for easy browsing.
    """
    from backend.services import news_scoring_service
    
    articles = await rss_service.get_recent_articles(db, limit)
    
    # Convert to dicts for scoring
    article_dicts = [
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
    
    # Score and group
    scored = await news_scoring_service.batch_score_articles(article_dicts, use_ai=False)
    grouped = news_scoring_service.group_articles_by_category(scored)
    
    return {
        "groups": grouped,
        "total_count": len(article_dicts),
        "categories": list(grouped.keys())
    }


@router.post("/news/ai-score")
async def ai_score_news(
    limit: int = 20,
    db: AsyncSession = Depends(get_db)
):
    """
    Score news articles using AI for deeper analysis.
    Limited to 20 articles due to API costs.
    """
    from backend.services import news_scoring_service
    
    articles = await rss_service.get_recent_articles(db, limit)
    
    article_dicts = [
        {
            "id": a.id,
            "title": a.title,
            "summary": a.summary,
            "url": a.url,
            "feed_name": a.feed.name if a.feed else None,
        }
        for a in articles
    ]
    
    # Use AI scoring
    scored = await news_scoring_service.batch_score_articles(article_dicts, use_ai=True)
    
    return scored


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


@router.post("/ads/upload-video")
async def upload_video_ad(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    niche_id: Optional[int] = Form(None),
    source: Optional[str] = Form(None),
    performance_notes: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload a video ad, transcribe it, and save the transcription as ad copy.
    The video is NOT stored - only the transcribed text.
    
    Supports: mp4, mov, avi, mkv, webm, mp3, wav, m4a, ogg
    Max size: 25MB
    """
    # Validate file size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, 
            detail=f"File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB"
        )
    
    # Transcribe the video
    try:
        transcription = await transcription_service.transcribe_video(content, file.filename)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")
    
    # Format and save as ad
    ad_content = transcription_service.format_transcription_as_ad(transcription)
    
    if not ad_content.strip():
        raise HTTPException(status_code=400, detail="No speech detected in the video")
    
    # Create the ad with transcribed content
    new_ad = await ad_service.create_ad(
        db,
        content=ad_content,
        title=title or f"Video Ad - {file.filename}",
        niche_id=niche_id,
        source=source or "Video Upload (Transcribed)",
        performance_notes=performance_notes
    )
    
    return {
        "id": new_ad.id,
        "message": "Video transcribed and saved as ad",
        "transcription": ad_content,
        "duration_seconds": transcription.get("duration"),
        "language": transcription.get("language")
    }


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


# ============== Chat/Assistant Routes ==============

@router.post("/chat")
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)):
    """
    Send a message to the AI assistant and get a response.
    Maintains conversation history for context.
    Can reference specific ads and articles for context.
    """
    import uuid
    from sqlalchemy import select
    from backend.models import Ad, NewsArticle
    
    # Get or create conversation
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    if conv_id not in conversations:
        conversations[conv_id] = []
    
    # Build context from database
    context = {}
    
    if request.niche_id:
        niche = await niche_service.get_niche_by_id(db, request.niche_id)
        if niche:
            context["niche"] = niche.name
    
    # Get pattern summary for context
    pattern_summary = await ad_service.get_pattern_summary(db, request.niche_id)
    if pattern_summary:
        context["patterns"] = pattern_summary
    
    # Get recent news headlines
    articles = await rss_service.get_recent_articles(db, limit=5)
    if articles:
        context["recent_news"] = [a.title for a in articles]
    
    # Fetch referenced ads if provided
    referenced_ads = []
    if request.ad_ids:
        for ad_id in request.ad_ids[:5]:  # Limit to 5 ads
            result = await db.execute(select(Ad).where(Ad.id == ad_id))
            ad = result.scalar_one_or_none()
            if ad:
                referenced_ads.append({
                    "id": ad.id,
                    "title": ad.title or f"Ad #{ad.id}",
                    "content": ad.content
                })
    
    if referenced_ads:
        context["referenced_ads"] = referenced_ads
    
    # Fetch referenced articles if provided
    referenced_articles = []
    if request.article_ids:
        for article_id in request.article_ids[:5]:  # Limit to 5 articles
            result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
            article = result.scalar_one_or_none()
            if article:
                referenced_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "trending_angles": article.trending_angles
                })
    
    if referenced_articles:
        context["referenced_articles"] = referenced_articles
    
    # Build the user message with reference indicators
    user_message = request.message
    if referenced_ads or referenced_articles:
        refs = []
        if referenced_ads:
            refs.append(f"{len(referenced_ads)} ad(s) attached")
        if referenced_articles:
            refs.append(f"{len(referenced_articles)} article(s) attached")
        user_message = f"[📎 {', '.join(refs)}]\n\n{request.message}"
    
    # Add user message to history
    conversations[conv_id].append({
        "role": "user",
        "content": user_message
    })
    
    # Get AI response
    try:
        response = await chat_service.chat_completion(
            messages=conversations[conv_id],
            context=context
        )
        
        # Add assistant response to history
        conversations[conv_id].append({
            "role": "assistant",
            "content": response
        })
        
        return {
            "conversation_id": conv_id,
            "response": response,
            "message_count": len(conversations[conv_id]),
            "referenced_ads": len(referenced_ads),
            "referenced_articles": len(referenced_articles)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/script")
async def generate_script(request: ScriptRequest, db: AsyncSession = Depends(get_db)):
    """
    Generate a full script (VSL, UGC, native ad, etc.)
    Can reference specific ads and articles for style/angle.
    """
    from sqlalchemy import select
    from backend.models import Ad, NewsArticle
    
    # Get niche
    niche = await niche_service.get_niche_by_id(db, request.niche_id)
    if not niche:
        raise HTTPException(status_code=404, detail="Niche not found")
    
    # Build context
    context = {"niche": niche.name}
    
    pattern_summary = await ad_service.get_pattern_summary(db, request.niche_id)
    if pattern_summary:
        context["patterns"] = pattern_summary
    
    articles = await rss_service.get_recent_articles(db, limit=5)
    if articles:
        context["recent_news"] = [a.title for a in articles]
    
    # Fetch referenced ads if provided
    if request.ad_ids:
        referenced_ads = []
        for ad_id in request.ad_ids[:5]:
            result = await db.execute(select(Ad).where(Ad.id == ad_id))
            ad = result.scalar_one_or_none()
            if ad:
                referenced_ads.append({
                    "id": ad.id,
                    "title": ad.title or f"Ad #{ad.id}",
                    "content": ad.content
                })
        if referenced_ads:
            context["referenced_ads"] = referenced_ads
    
    # Fetch referenced articles if provided
    if request.article_ids:
        referenced_articles = []
        for article_id in request.article_ids[:5]:
            result = await db.execute(select(NewsArticle).where(NewsArticle.id == article_id))
            article = result.scalar_one_or_none()
            if article:
                referenced_articles.append({
                    "id": article.id,
                    "title": article.title,
                    "summary": article.summary or "",
                    "trending_angles": article.trending_angles
                })
        if referenced_articles:
            context["referenced_articles"] = referenced_articles
    
    try:
        script = await chat_service.generate_script(
            script_type=request.script_type,
            niche=niche.name,
            topic=request.topic,
            context=context,
            additional_instructions=request.additional_instructions
        )
        
        return {
            "script": script,
            "script_type": request.script_type,
            "niche": niche.name,
            "topic": request.topic
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation history"""
    if conversation_id not in conversations:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return {
        "conversation_id": conversation_id,
        "messages": conversations[conversation_id]
    }


@router.delete("/chat/conversations/{conversation_id}")
async def clear_conversation(conversation_id: str):
    """Clear/reset a conversation"""
    if conversation_id in conversations:
        del conversations[conversation_id]
    
    return {"message": "Conversation cleared"}


@router.get("/chat/script-types")
async def get_script_types():
    """Get available script types"""
    return {
        "script_types": [
            {"id": "vsl", "name": "Video Sales Letter (VSL)", "description": "Long-form persuasive video script"},
            {"id": "ugc", "name": "UGC Script", "description": "User-generated content style, 30-60 seconds"},
            {"id": "native", "name": "Native Ad", "description": "Editorial style, feels like content"},
            {"id": "hooks", "name": "Hook Pack", "description": "10 scroll-stopping hooks"},
            {"id": "email", "name": "Email Sequence", "description": "3-email promotional sequence"},
        ]
    }
