"""
Affiliate Copywriter OS - News Scoring Service
Intelligently scores and filters news for copywriting potential
"""
import json
import re
from typing import Optional
from backend.config import settings

# Initialize AI clients
openai_client = None
anthropic_client = None

if settings.openai_api_key:
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

if settings.anthropic_api_key:
    from anthropic import AsyncAnthropic
    anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


# Keywords that indicate high copywriting potential
HOOK_INDICATORS = [
    # Emotional triggers
    "shocking", "surprising", "secret", "hidden", "revealed", "exposed",
    "warning", "alert", "urgent", "breaking", "exclusive", "insider",
    
    # Numbers/specificity
    "how to", "ways to", "reasons why", "mistakes", "tips", "hacks",
    "%", "million", "billion", "thousands",
    
    # Controversy/curiosity
    "controversial", "debate", "truth about", "myth", "actually",
    "you won't believe", "never", "always", "everyone", "no one",
    
    # Fear/urgency
    "deadline", "expires", "limited", "last chance", "before it's too late",
    "risk", "danger", "crisis", "surge", "spike", "plunge", "crash",
    
    # Benefit-driven
    "save", "free", "discount", "deal", "cheap", "afford",
    "easy", "simple", "fast", "instant", "guaranteed",
    
    # Insurance/Finance specific
    "rates", "premium", "coverage", "claim", "policy", "quote",
    "mortgage", "refinance", "interest rate", "fed", "inflation",
    "homeowner", "driver", "accident", "storm", "disaster"
]

# Categories for grouping
CATEGORIES = {
    "money_saving": ["save", "discount", "cheap", "deal", "free", "afford", "budget", "cost"],
    "rates_economy": ["rate", "interest", "fed", "inflation", "economy", "market", "price"],
    "insurance_news": ["insurance", "coverage", "claim", "policy", "premium", "deductible"],
    "home_property": ["home", "house", "property", "mortgage", "refinance", "real estate", "housing"],
    "auto_driving": ["car", "auto", "vehicle", "driver", "driving", "accident", "traffic"],
    "weather_disaster": ["storm", "hurricane", "flood", "fire", "disaster", "weather", "climate"],
    "trending_viral": ["viral", "trending", "popular", "everyone", "millions"],
    "consumer_tips": ["tips", "hack", "trick", "secret", "how to", "guide", "mistakes"],
}


def quick_score_article(title: str, summary: str = "") -> dict:
    """
    Quick scoring without AI - uses keyword matching.
    Returns score and detected categories.
    """
    text = f"{title} {summary}".lower()
    
    # Count hook indicators
    hook_count = sum(1 for indicator in HOOK_INDICATORS if indicator in text)
    
    # Detect categories
    detected_categories = []
    for category, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            detected_categories.append(category)
    
    # Calculate base score (0-100)
    score = min(100, hook_count * 15 + len(detected_categories) * 10)
    
    # Bonus for numbers (specificity)
    if re.search(r'\d+%|\$\d+|\d+ (million|billion|thousand)', text):
        score = min(100, score + 15)
    
    # Bonus for questions (curiosity)
    if "?" in title:
        score = min(100, score + 10)
    
    return {
        "score": score,
        "categories": detected_categories,
        "hook_indicators": hook_count
    }


async def ai_score_article(title: str, summary: str = "") -> dict:
    """
    AI-powered scoring for deeper analysis.
    Returns detailed scoring and hook ideas.
    """
    if not (openai_client or anthropic_client):
        return quick_score_article(title, summary)
    
    prompt = f"""Analyze this news article for affiliate copywriting potential.

HEADLINE: {title}
SUMMARY: {summary[:500] if summary else 'N/A'}

Score this article on a scale of 0-100 for copywriting potential, considering:
- Does it have an emotional hook?
- Is it about something people care about right now?
- Could it be used as a news angle for insurance/finance ads?
- Does it create curiosity, fear, or desire?

Return JSON only:
{{
    "score": 0-100,
    "categories": ["list", "of", "relevant", "categories"],
    "emotional_triggers": ["list", "of", "emotions", "this", "evokes"],
    "hook_potential": "brief explanation of how this could be used for ad hooks",
    "copy_angle": "one sentence ad angle inspired by this"
}}"""

    try:
        if settings.ai_provider == "anthropic" and anthropic_client:
            response = await anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=500,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
        elif openai_client:
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use mini for cost efficiency on scoring
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=500
            )
            result = response.choices[0].message.content
        else:
            return quick_score_article(title, summary)
        
        # Parse JSON
        result = result.strip()
        if result.startswith("```"):
            result = result.split("```")[1]
            if result.startswith("json"):
                result = result[4:]
        
        return json.loads(result)
    except Exception as e:
        print(f"AI scoring failed: {e}")
        return quick_score_article(title, summary)


async def batch_score_articles(articles: list[dict], use_ai: bool = False) -> list[dict]:
    """
    Score multiple articles efficiently.
    Uses quick scoring by default, AI scoring if enabled.
    """
    scored = []
    
    for article in articles:
        title = article.get("title", "")
        summary = article.get("summary", "")
        
        if use_ai:
            score_data = await ai_score_article(title, summary)
        else:
            score_data = quick_score_article(title, summary)
        
        scored.append({
            **article,
            "relevance_score": score_data.get("score", 0),
            "categories": score_data.get("categories", []),
            "emotional_triggers": score_data.get("emotional_triggers", []),
            "hook_potential": score_data.get("hook_potential", ""),
            "copy_angle": score_data.get("copy_angle", "")
        })
    
    # Sort by score descending
    scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return scored


def group_articles_by_category(articles: list[dict]) -> dict:
    """
    Group articles by their detected categories.
    """
    groups = {
        "🔥 High Potential": [],
        "💰 Money & Savings": [],
        "📈 Rates & Economy": [],
        "🛡️ Insurance News": [],
        "🏠 Home & Property": [],
        "🚗 Auto & Driving": [],
        "⛈️ Weather & Disasters": [],
        "💡 Tips & Hacks": [],
        "📰 Other News": []
    }
    
    category_map = {
        "money_saving": "💰 Money & Savings",
        "rates_economy": "📈 Rates & Economy",
        "insurance_news": "🛡️ Insurance News",
        "home_property": "🏠 Home & Property",
        "auto_driving": "🚗 Auto & Driving",
        "weather_disaster": "⛈️ Weather & Disasters",
        "consumer_tips": "💡 Tips & Hacks",
        "trending_viral": "🔥 High Potential"
    }
    
    for article in articles:
        score = article.get("relevance_score", 0)
        categories = article.get("categories", [])
        
        # High score goes to top
        if score >= 60:
            groups["🔥 High Potential"].append(article)
        elif categories:
            # Put in first matching category
            placed = False
            for cat in categories:
                if cat in category_map:
                    groups[category_map[cat]].append(article)
                    placed = True
                    break
            if not placed:
                groups["📰 Other News"].append(article)
        else:
            groups["📰 Other News"].append(article)
    
    # Remove empty groups
    return {k: v for k, v in groups.items() if v}
