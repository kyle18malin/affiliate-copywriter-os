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


# HIGH VALUE - Controversial, emotional, fear/anger inducing (worth 20+ points each)
HIGH_VALUE_TRIGGERS = [
    # Political drama (gets people ANGRY)
    "trump", "maga", "biden", "democrats destroy", "republicans destroy",
    "leftist", "right-wing", "woke", "anti-woke", "liberal tears",
    "conservative", "radical", "extremist", "socialist", "fascist",
    
    # Government outrage
    "shutdown", "default", "debt ceiling", "government waste",
    "taxpayer money", "big government", "deep state", "corruption",
    "scandal", "cover-up", "exposed", "caught", "busted",
    "investigation", "indicted", "arrested", "charged", "guilty",
    
    # Fear/danger/threat
    "warning", "alert", "danger", "threat", "risk", "unsafe",
    "deadly", "killed", "dies", "death", "fatal", "victims",
    "crash", "collapse", "crisis", "emergency", "disaster",
    "scam", "fraud", "ripoff", "stealing", "theft", "hacked",
    
    # Money fears (losing money = high engagement)
    "skyrocket", "surge", "spike", "soar", "explode", "double", "triple",
    "plunge", "crash", "tank", "collapse", "recession", "depression",
    "can't afford", "unaffordable", "priced out", "struggling",
    "layoffs", "fired", "unemployed", "job cuts", "hiring freeze",
    
    # Outrage bait
    "outrage", "furious", "angry", "slammed", "blasted", "ripped",
    "destroyed", "obliterated", "humiliated", "embarrassed",
    "caught on camera", "leaked", "secretly", "hidden",
    "you won't believe", "exposed", "the truth about", "exposed",
    "lied", "lying", "lies", "deceived", "betrayed", "backstabbed",
    
    # Breaking/urgent
    "breaking", "just in", "urgent", "developing", "happening now",
    "exclusive", "first look", "insider", "leaked",
]

# MEDIUM VALUE - Good hooks but less emotional (worth 10-15 points each)
MEDIUM_VALUE_TRIGGERS = [
    # Insurance/finance specifics
    "rates rising", "premiums", "insurance cost", "coverage denied",
    "claim rejected", "rate hike", "price increase",
    "mortgage rates", "interest rates", "fed raises", "fed cuts",
    "inflation", "cost of living", "prices",
    
    # Consumer angles
    "hidden fees", "fine print", "gotcha", "trap", "trick",
    "overcharged", "ripped off", "fighting back",
    
    # Health scares
    "recall", "contaminated", "dangerous", "side effects",
    "cancer", "disease", "outbreak", "virus", "epidemic",
    
    # Weather/disasters  
    "hurricane", "tornado", "flood", "wildfire", "earthquake",
    "storm", "devastation", "damage", "destroyed homes",
    
    # Crime/safety
    "crime", "robbery", "assault", "shooting", "murder",
    "unsafe", "protect yourself", "home invasion",
]

# LOW VALUE - Generic stuff (worth 5 points max)
LOW_VALUE_TRIGGERS = [
    "how to", "tips", "guide", "tutorial", "ways to",
    "best", "top", "review", "comparison",
]

# NEGATIVE - Penalize boring/generic content (subtract points)
BORING_INDICATORS = [
    "megathread", "weekly thread", "daily thread", "discussion thread",
    "question", "advice", "opinion", "thoughts", "help me",
    "should i", "is it worth", "what do you think",
    "eli5", "ama", "rant", "vent", "update",
    "comprehensive list", "resource list", "guide to",
    "beginner", "getting started", "101", "basics",
    "reminder", "psa", "fyi", "til",
]

# Categories for grouping
CATEGORIES = {
    "politics_drama": ["trump", "biden", "maga", "democrat", "republican", "congress", "senate", 
                       "shutdown", "scandal", "investigation", "indicted", "woke", "liberal", "conservative"],
    "money_fears": ["recession", "inflation", "layoffs", "unemployment", "crash", "plunge", 
                    "can't afford", "skyrocket", "surge", "spike", "priced out", "struggling"],
    "scams_warnings": ["scam", "fraud", "warning", "alert", "ripoff", "hacked", "stolen", 
                       "exposed", "caught", "busted", "hidden fees"],
    "rates_economy": ["rate", "interest", "fed", "mortgage rate", "insurance rate", "premium", "price hike"],
    "insurance_news": ["insurance", "coverage", "claim denied", "policy", "premium", "deductible"],
    "crime_safety": ["crime", "shooting", "murder", "robbery", "assault", "arrest", "killed", "death"],
    "disasters": ["hurricane", "tornado", "flood", "wildfire", "earthquake", "storm", "devastation", "damage"],
    "health_scares": ["recall", "cancer", "disease", "outbreak", "contaminated", "dangerous", "side effects"],
    "outrage": ["outrage", "furious", "slammed", "blasted", "destroyed", "lied", "betrayed", "caught on camera"],
}


def quick_score_article(title: str, summary: str = "") -> dict:
    """
    Quick scoring without AI - uses keyword matching with weighted categories.
    Prioritizes controversial, emotional, fear/anger content.
    Penalizes generic/bland content.
    """
    text = f"{title} {summary}".lower()
    title_lower = title.lower()
    
    score = 0
    detected_categories = []
    emotional_triggers = []
    
    # HIGH VALUE triggers (20 points each, max 60 from this category)
    high_value_count = 0
    for trigger in HIGH_VALUE_TRIGGERS:
        if trigger in text:
            high_value_count += 1
            if high_value_count <= 3:  # Cap at 3
                score += 20
            if trigger in ["trump", "maga", "biden", "shutdown", "scandal", "crash", "scam", "warning"]:
                emotional_triggers.append(trigger)
    
    # MEDIUM VALUE triggers (12 points each, max 36)
    medium_value_count = 0
    for trigger in MEDIUM_VALUE_TRIGGERS:
        if trigger in text:
            medium_value_count += 1
            if medium_value_count <= 3:
                score += 12
    
    # LOW VALUE triggers (only 3 points each)
    for trigger in LOW_VALUE_TRIGGERS:
        if trigger in text:
            score += 3
    
    # PENALTIES for boring/generic content
    for boring in BORING_INDICATORS:
        if boring in title_lower:  # Only penalize if in title
            score -= 25  # Heavy penalty
    
    # Penalty for questions in title (usually advice-seeking, not news)
    if title_lower.startswith(("should i", "is it", "what do", "how do i", "can i", "would it")):
        score -= 30
    
    # Penalty for Reddit-style personal posts
    if any(x in title_lower for x in ["my ", "i'm ", "i am ", "i have ", "i just ", "i need "]):
        score -= 20
    
    # BONUSES
    # Specific numbers in negative context (fear-inducing)
    if re.search(r'\d+%\s*(increase|rise|jump|surge|spike|hike)', text):
        score += 15
    if re.search(r'\$[\d,]+\s*(lost|stolen|scam|fraud)', text):
        score += 15
    if re.search(r'\d+\s*(killed|dead|deaths|victims|injured)', text):
        score += 20
    
    # Bonus for ALL CAPS words (clickbait style)
    if re.search(r'\b[A-Z]{4,}\b', title):
        score += 10
    
    # Bonus for exclamation or strong punctuation
    if "!" in title:
        score += 5
    
    # Detect categories
    for category, keywords in CATEGORIES.items():
        if any(kw in text for kw in keywords):
            detected_categories.append(category)
    
    # Bonus for being in high-engagement categories
    high_engagement_cats = ["politics_drama", "money_fears", "scams_warnings", "crime_safety", "outrage"]
    for cat in detected_categories:
        if cat in high_engagement_cats:
            score += 10
    
    # Clamp score between 0-100
    score = max(0, min(100, score))
    
    return {
        "score": score,
        "categories": detected_categories,
        "emotional_triggers": emotional_triggers,
        "high_value_count": high_value_count,
        "is_generic": score < 20
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
    Prioritizes controversial/emotional categories first.
    """
    groups = {
        "🔥 Hot Takes": [],           # Score 70+
        "🏛️ Political Drama": [],     # Trump, Biden, Congress battles
        "💸 Money Fears": [],         # Recession, inflation, layoffs
        "⚠️ Scams & Warnings": [],    # Fraud, alerts, danger
        "😡 Outrage": [],             # People mad about stuff
        "🔪 Crime & Safety": [],      # Crime, shootings, arrests
        "📈 Rates & Economy": [],     # Interest rates, fed, markets
        "🛡️ Insurance News": [],      # Insurance specific
        "⛈️ Disasters": [],           # Weather, natural disasters
        "🏥 Health Scares": [],       # Recalls, outbreaks
        "📰 Other": []                # Everything else
    }
    
    category_map = {
        "politics_drama": "🏛️ Political Drama",
        "money_fears": "💸 Money Fears",
        "scams_warnings": "⚠️ Scams & Warnings",
        "outrage": "😡 Outrage",
        "crime_safety": "🔪 Crime & Safety",
        "rates_economy": "📈 Rates & Economy",
        "insurance_news": "🛡️ Insurance News",
        "disasters": "⛈️ Disasters",
        "health_scares": "🏥 Health Scares",
    }
    
    for article in articles:
        score = article.get("relevance_score", 0)
        categories = article.get("categories", [])
        
        # High score goes to Hot Takes
        if score >= 70:
            groups["🔥 Hot Takes"].append(article)
        elif categories:
            # Put in first matching category (priority order)
            placed = False
            for cat in categories:
                if cat in category_map:
                    groups[category_map[cat]].append(article)
                    placed = True
                    break
            if not placed:
                groups["📰 Other"].append(article)
        else:
            groups["📰 Other"].append(article)
    
    # Remove empty groups and sort by category priority
    priority_order = [
        "🔥 Hot Takes", "🏛️ Political Drama", "💸 Money Fears", 
        "⚠️ Scams & Warnings", "😡 Outrage", "🔪 Crime & Safety",
        "📈 Rates & Economy", "🛡️ Insurance News", "⛈️ Disasters",
        "🏥 Health Scares", "📰 Other"
    ]
    
    result = {}
    for key in priority_order:
        if key in groups and groups[key]:
            result[key] = groups[key]
    
    return result
