"""
Affiliate Copywriter OS - Niche Service
Handles niche management
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.models import Niche
from backend.config import settings


async def init_default_niches(db: AsyncSession):
    """Initialize database with default niches"""
    for niche_name in settings.default_niches:
        result = await db.execute(
            select(Niche).where(Niche.name == niche_name)
        )
        existing = result.scalar_one_or_none()
        
        if not existing:
            niche = Niche(name=niche_name)
            db.add(niche)
    
    await db.commit()


async def get_all_niches(db: AsyncSession) -> list[Niche]:
    """Get all niches"""
    result = await db.execute(select(Niche).order_by(Niche.name))
    return list(result.scalars().all())


async def create_niche(db: AsyncSession, name: str, description: str = None) -> Niche:
    """Create a new niche"""
    niche = Niche(name=name, description=description)
    db.add(niche)
    await db.commit()
    await db.refresh(niche)
    return niche


async def get_niche_by_id(db: AsyncSession, niche_id: int) -> Niche:
    """Get a niche by ID"""
    result = await db.execute(select(Niche).where(Niche.id == niche_id))
    return result.scalar_one_or_none()
