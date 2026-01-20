"""
Affiliate Copywriter OS - Ad Analysis Service
Handles uploading and analyzing winning ads
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import Optional
from backend.models import Ad, AdPattern, Niche


async def create_ad(
    db: AsyncSession,
    content: str,
    title: str = None,
    niche_id: int = None,
    source: str = None,
    performance_notes: str = None
) -> Ad:
    """Create a new ad entry"""
    ad = Ad(
        content=content,
        title=title,
        niche_id=niche_id,
        source=source,
        performance_notes=performance_notes
    )
    db.add(ad)
    await db.commit()
    await db.refresh(ad)
    return ad


async def get_all_ads(db: AsyncSession, niche_id: int = None) -> list[Ad]:
    """Get all ads, optionally filtered by niche"""
    query = select(Ad).options(selectinload(Ad.niche), selectinload(Ad.patterns))
    
    if niche_id:
        query = query.where(Ad.niche_id == niche_id)
    
    query = query.order_by(Ad.created_at.desc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_ad_by_id(db: AsyncSession, ad_id: int) -> Optional[Ad]:
    """Get a specific ad by ID"""
    result = await db.execute(
        select(Ad)
        .options(selectinload(Ad.niche), selectinload(Ad.patterns))
        .where(Ad.id == ad_id)
    )
    return result.scalar_one_or_none()


async def save_ad_patterns(db: AsyncSession, ad_id: int, patterns: dict) -> AdPattern:
    """Save extracted patterns for an ad"""
    pattern = AdPattern(
        ad_id=ad_id,
        hook_structure=patterns.get("hook_structure"),
        hook_example=patterns.get("hook_example"),
        emotional_triggers=patterns.get("emotional_triggers"),
        curiosity_gaps=patterns.get("curiosity_gaps"),
        power_words=patterns.get("power_words"),
        cta_pattern=patterns.get("cta_pattern"),
        persuasion_techniques=patterns.get("persuasion_techniques")
    )
    db.add(pattern)
    await db.commit()
    await db.refresh(pattern)
    return pattern


async def get_all_patterns(db: AsyncSession, niche_id: int = None, limit: int = 100) -> list[AdPattern]:
    """
    Get all ad patterns for hook generation.
    If niche_id provided, returns niche-specific patterns first, then general patterns.
    """
    if niche_id:
        # Get niche-specific patterns
        niche_result = await db.execute(
            select(AdPattern)
            .join(Ad)
            .where(Ad.niche_id == niche_id)
            .limit(limit)
        )
        niche_patterns = list(niche_result.scalars().all())
        
        # Get general patterns (no niche or different niche)
        remaining = limit - len(niche_patterns)
        if remaining > 0:
            general_result = await db.execute(
                select(AdPattern)
                .join(Ad)
                .where((Ad.niche_id.is_(None)) | (Ad.niche_id != niche_id))
                .limit(remaining)
            )
            general_patterns = list(general_result.scalars().all())
            return niche_patterns + general_patterns
        
        return niche_patterns
    else:
        # Get all patterns
        result = await db.execute(select(AdPattern).limit(limit))
        return list(result.scalars().all())


async def get_pattern_summary(db: AsyncSession, niche_id: int = None) -> dict:
    """Get aggregated summary of all patterns for AI context"""
    patterns = await get_all_patterns(db, niche_id)
    
    summary = {
        "hook_structures": [],
        "hook_examples": [],
        "all_emotional_triggers": set(),
        "all_curiosity_gaps": set(),
        "all_power_words": set(),
        "cta_patterns": [],
        "all_persuasion_techniques": set()
    }
    
    for p in patterns:
        if p.hook_structure:
            summary["hook_structures"].append(p.hook_structure)
        if p.hook_example:
            summary["hook_examples"].append(p.hook_example)
        if p.emotional_triggers:
            summary["all_emotional_triggers"].update(p.emotional_triggers)
        if p.curiosity_gaps:
            summary["all_curiosity_gaps"].update(p.curiosity_gaps)
        if p.power_words:
            summary["all_power_words"].update(p.power_words)
        if p.cta_pattern:
            summary["cta_patterns"].append(p.cta_pattern)
        if p.persuasion_techniques:
            summary["all_persuasion_techniques"].update(p.persuasion_techniques)
    
    # Convert sets to lists for JSON serialization
    summary["all_emotional_triggers"] = list(summary["all_emotional_triggers"])
    summary["all_curiosity_gaps"] = list(summary["all_curiosity_gaps"])
    summary["all_power_words"] = list(summary["all_power_words"])
    summary["all_persuasion_techniques"] = list(summary["all_persuasion_techniques"])
    
    return summary
