"""
Affiliate Copywriter OS - Database Models
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from backend.database import Base


class Niche(Base):
    """Niches for organizing content (Auto Insurance, Home Insurance, Refi, etc.)"""
    __tablename__ = "niches"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    ads = relationship("Ad", back_populates="niche")
    generated_hooks = relationship("GeneratedHook", back_populates="niche")


class RSSFeed(Base):
    """RSS feeds for news aggregation - Universal across all niches"""
    __tablename__ = "rss_feeds"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    url = Column(String(500), unique=True, nullable=False)
    category = Column(String(100), nullable=True)  # General category (news, finance, lifestyle)
    is_active = Column(Boolean, default=True)
    last_fetched = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    articles = relationship("NewsArticle", back_populates="feed")


class NewsArticle(Base):
    """News articles scraped from RSS feeds"""
    __tablename__ = "news_articles"
    
    id = Column(Integer, primary_key=True, index=True)
    feed_id = Column(Integer, ForeignKey("rss_feeds.id"), nullable=False)
    title = Column(String(500), nullable=False)
    summary = Column(Text, nullable=True)
    content = Column(Text, nullable=True)
    url = Column(String(500), unique=True, nullable=False)
    published_at = Column(DateTime(timezone=True), nullable=True)
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # AI-extracted insights
    trending_angles = Column(JSON, nullable=True)  # List of angles/hooks from this article
    emotional_triggers = Column(JSON, nullable=True)  # Emotions this article taps into
    relevance_score = Column(Float, nullable=True)  # How relevant for ad creation
    
    # Relationships
    feed = relationship("RSSFeed", back_populates="articles")


class Ad(Base):
    """Uploaded winning ads for analysis"""
    __tablename__ = "ads"
    
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=True)  # Optional niche tag
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)  # The actual ad copy
    source = Column(String(200), nullable=True)  # Where it came from
    performance_notes = Column(Text, nullable=True)  # Why it's a winner
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    niche = relationship("Niche", back_populates="ads")
    patterns = relationship("AdPattern", back_populates="ad")


class AdPattern(Base):
    """Extracted patterns from winning ads - UNIVERSAL across all niches"""
    __tablename__ = "ad_patterns"
    
    id = Column(Integer, primary_key=True, index=True)
    ad_id = Column(Integer, ForeignKey("ads.id"), nullable=False)
    
    # Universal patterns extracted from ads
    hook_structure = Column(Text, nullable=True)  # The formula/structure of the hook
    hook_example = Column(Text, nullable=True)  # The actual hook text
    emotional_triggers = Column(JSON, nullable=True)  # List of emotions used
    curiosity_gaps = Column(JSON, nullable=True)  # Curiosity techniques used
    power_words = Column(JSON, nullable=True)  # Impactful words identified
    cta_pattern = Column(Text, nullable=True)  # Call-to-action structure
    persuasion_techniques = Column(JSON, nullable=True)  # Techniques like scarcity, social proof
    
    # Relationships
    ad = relationship("Ad", back_populates="patterns")


class GeneratedHook(Base):
    """AI-generated hooks"""
    __tablename__ = "generated_hooks"
    
    id = Column(Integer, primary_key=True, index=True)
    niche_id = Column(Integer, ForeignKey("niches.id"), nullable=False)
    hook_text = Column(Text, nullable=False)
    hook_type = Column(String(100), nullable=True)  # curiosity, fear, benefit, etc.
    inspiration_source = Column(Text, nullable=True)  # What news/ad inspired this
    news_angle = Column(Text, nullable=True)  # The trending angle used
    ad_patterns_used = Column(JSON, nullable=True)  # Which patterns influenced this
    rating = Column(Integer, nullable=True)  # User rating 1-5
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    niche = relationship("Niche", back_populates="generated_hooks")
