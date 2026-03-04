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

# VANILLA FINANCIAL CONTENT - Nobody cares about small rate changes
BORING_FINANCIAL = [
    "rate unchanged", "rates steady", "holds steady", "remains unchanged",
    "slight increase", "slight decrease", "minor change", "modest",
    "quarterly report", "earnings call", "fiscal year",
    "basis points", "bps", "0.25%", "quarter point",
    "fed meeting", "fomc minutes", "economic data",
    "market opens", "futures point", "premarket",
    "analysts expect", "consensus estimate", "forecast",
    "weekly jobless", "initial claims", "continuing claims",
]

# Headlines that are just corporate PR / boring news
BORING_CORPORATE = [
    "announces partnership", "strategic partnership", "collaboration with",
    "expands into", "launches new", "introduces new", "unveils",
    "appoints new", "names new ceo", "executive appointment",
    "quarterly results", "beats estimates", "misses estimates",
    "guidance", "outlook", "reaffirms", "maintains",
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
    "reddit_trending": ["reddit", "r/", "upvote", "trending on reddit"],
}

# Subreddits that are GOLDMINES for emotional/viral content
# Tier 1: VIRAL VIDEO / FREAKOUT / DRAMA (highest engagement)
VIRAL_SUBREDDITS = [
    "publicfreakout", "facepalm", "whatcouldgowrong", "instant_regret",
    "wellthatsucks", "therewasanattempt", "abruptchaos", "crazyfuckingvideos",
    "nextfuckinglevel", "damnthatsinteresting", "idiotsincars", "dashcam",
    "tiktokcringe", "cringepics", "sadcringe", "trashy"
]

# Tier 2: JUSTICE / REVENGE / KARMA (satisfying emotional payoff)
JUSTICE_SUBREDDITS = [
    "justiceserved", "maliciouscompliance", "pettyrevenge", "prorevenge",
    "nuclearrevenge", "leopardsatemyface", "byebyejob", "fuckyouinparticular",
    "choosingbeggars", "entitledparents", "entitledpeople", "fuckyoukaren",
    "idontworkherelady", "iamatotalpieceofshit"
]

# Tier 3: CORPORATE HATE / DYSTOPIA (anti-establishment rage)
CORPORATE_HATE_SUBREDDITS = [
    "antiwork", "workreform", "latestagecapitalism", "aboringdystopia",
    "lostgeneration", "recruitinghell", "assholedesign", "hailcorporate"
]

# Tier 4: MONEY / HOUSING CRISIS (financial fear)
MONEY_FEAR_SUBREDDITS = [
    "wallstreetbets", "povertyfinance", "personalfinance", "studentloans",
    "debt", "fluentinfinance", "economy", "rebubble", "realestate",
    "firsttimehomebuyer", "scams"
]

# Tier 5: STORIES / CONFESSIONS (raw emotional content)
STORY_SUBREDDITS = [
    "tifu", "confessions", "trueoffmychest", "amitheasshole",
    "relationship_advice", "bestofredditorupdates", "offmychest",
    "unpopularopinion", "the10thdentist", "legaladvice", "bestoflegaladvice"
]

# Tier 6: NEWS (current events)
NEWS_SUBREDDITS = [
    "news", "worldnews", "politics", "conservative", "liberal",
    "nottheonion", "outoftheloop", "subredditdrama", "hobbydrama"
]

# Combined high-value list
HIGH_VALUE_SUBREDDITS = (
    VIRAL_SUBREDDITS + JUSTICE_SUBREDDITS + CORPORATE_HATE_SUBREDDITS + 
    MONEY_FEAR_SUBREDDITS + STORY_SUBREDDITS + NEWS_SUBREDDITS +
    ["insurance", "mildlyinfuriating", "extremelyinfuriating", "rage", "agedlikemilk"]
)

# Subreddits with mostly boring advice-seeking (penalize)
LOW_VALUE_SUBREDDITS = [
    "eli5", "advice", "askreddit", "askscience", "askhistorians",
    "explainlikeimfive", "todayilearned", "lifeprotips", "youshouldknow"
]


def quick_score_article(title: str, summary: str = "", feed_name: str = "", url: str = "") -> dict:
    """
    Quick scoring without AI - uses keyword matching with weighted categories.
    Prioritizes controversial, emotional, fear/anger content.
    Penalizes generic/bland content.
    
    Special handling for Reddit content:
    - Detects subreddit from feed name or URL
    - Boosts high-value subreddits
    - Extracts engagement signals
    """
    text = f"{title} {summary}".lower()
    title_lower = title.lower()
    feed_lower = feed_name.lower()
    url_lower = url.lower()
    
    score = 0
    detected_categories = []
    emotional_triggers = []
    is_reddit = False
    subreddit = None
    
    # Detect if this is Reddit content
    if "reddit" in feed_lower or "reddit.com" in url_lower or "r/" in feed_lower:
        is_reddit = True
        detected_categories.append("reddit_trending")
        
        # Extract subreddit name
        subreddit_match = re.search(r'r/(\w+)', url_lower) or re.search(r'reddit.*?-\s*(\w+)', feed_lower, re.IGNORECASE)
        if subreddit_match:
            subreddit = subreddit_match.group(1).lower()
    
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
    # But REDUCE penalties for Reddit news subreddits (they post real news)
    is_news_subreddit = subreddit in ["news", "worldnews", "politics", "conservative", "personalfinance", "antiwork"]
    penalty_multiplier = 0.3 if is_news_subreddit else 1.0
    
    for boring in BORING_INDICATORS:
        if boring in title_lower:  # Only penalize if in title
            score -= int(25 * penalty_multiplier)
    
    # HEAVY PENALTY for vanilla financial content (nobody cares about small rate changes)
    for boring_fin in BORING_FINANCIAL:
        if boring_fin in text:
            score -= 35  # Heavy penalty - this is useless for copy
    
    # HEAVY PENALTY for boring corporate PR
    for boring_corp in BORING_CORPORATE:
        if boring_corp in text:
            score -= 30
    
    # Penalty for questions in title (usually advice-seeking, not news)
    # Reduced penalty for certain subreddits that have good question content
    if title_lower.startswith(("should i", "is it", "what do", "how do i", "can i", "would it")):
        if subreddit not in ["nostupidquestions", "youshouldknow", "lifeprotips"]:
            score -= int(30 * penalty_multiplier)
    
    # Penalty for Reddit-style personal posts - but NOT for emotional subreddits
    emotional_story_subs = ["trueoffmychest", "amitheasshole", "antiwork", "povertyfinance", "rant", "tifu", "confessions"]
    if any(x in title_lower for x in ["my ", "i'm ", "i am ", "i have ", "i just ", "i need "]):
        if subreddit in emotional_story_subs:
            # These personal stories are GOLDMINES for emotional hooks
            score += 10  # BONUS instead of penalty!
            emotional_triggers.append("personal_story")
        else:
            score -= 20
    
    # REDDIT-SPECIFIC BONUSES
    if is_reddit:
        # TIER 1: Viral video/freakout subreddits (highest value - proven viral content)
        if subreddit in VIRAL_SUBREDDITS:
            score += 30
            emotional_triggers.append("viral_video")
        
        # TIER 2: Justice/revenge subreddits (high emotional payoff)
        elif subreddit in JUSTICE_SUBREDDITS:
            score += 25
            emotional_triggers.append("justice")
        
        # TIER 3: Corporate hate (rage-inducing)
        elif subreddit in CORPORATE_HATE_SUBREDDITS:
            score += 25
            emotional_triggers.append("corporate_rage")
        
        # TIER 4: Money/housing crisis (fear-based)
        elif subreddit in MONEY_FEAR_SUBREDDITS:
            score += 20
            emotional_triggers.append("money_fear")
        
        # TIER 5: Stories/confessions (emotional hooks)
        elif subreddit in STORY_SUBREDDITS:
            score += 20
            emotional_triggers.append("personal_story")
        
        # TIER 6: News (current events)
        elif subreddit in NEWS_SUBREDDITS:
            score += 15
        
        # General high-value (catch-all)
        elif subreddit in HIGH_VALUE_SUBREDDITS:
            score += 15
            
        # Penalty for low-value subreddits
        if subreddit in LOW_VALUE_SUBREDDITS:
            score -= 20
        
        # Check for upvote counts in title or summary (sometimes included in RSS)
        upvote_match = re.search(r'(\d+)\s*(upvotes?|points?|karma)', text)
        if upvote_match:
            upvotes = int(upvote_match.group(1))
            if upvotes >= 50000:
                score += 35  # Mega viral
                emotional_triggers.append("mega_viral")
            elif upvotes >= 10000:
                score += 25  # Viral content
                emotional_triggers.append("viral")
            elif upvotes >= 5000:
                score += 15
            elif upvotes >= 1000:
                score += 10
        
        # Check for high comment counts (engagement signal = controversy)
        comment_match = re.search(r'(\d+)\s*comments?', text)
        if comment_match:
            comments = int(comment_match.group(1))
            if comments >= 5000:
                score += 25  # Extremely controversial
                emotional_triggers.append("massive_controversy")
            elif comments >= 1000:
                score += 15  # Highly discussed
                emotional_triggers.append("controversial")
            elif comments >= 500:
                score += 8
    
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
            if category not in detected_categories:
                detected_categories.append(category)
    
    # Bonus for being in high-engagement categories
    high_engagement_cats = ["politics_drama", "money_fears", "scams_warnings", "crime_safety", "outrage", "reddit_trending"]
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
        "is_generic": score < 20,
        "is_reddit": is_reddit,
        "subreddit": subreddit
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
        feed_name = article.get("feed_name", "")
        url = article.get("url", "")
        
        if use_ai:
            score_data = await ai_score_article(title, summary)
        else:
            score_data = quick_score_article(title, summary, feed_name, url)
        
        scored.append({
            **article,
            "relevance_score": score_data.get("score", 0),
            "categories": score_data.get("categories", []),
            "emotional_triggers": score_data.get("emotional_triggers", []),
            "hook_potential": score_data.get("hook_potential", ""),
            "copy_angle": score_data.get("copy_angle", ""),
            "is_reddit": score_data.get("is_reddit", False),
            "subreddit": score_data.get("subreddit", None)
        })
    
    # Sort by score descending
    scored.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)
    
    return scored


def group_articles_by_category(articles: list[dict]) -> dict:
    """
    Group articles by their detected categories.
    Prioritizes controversial/emotional categories first.
    Includes special Reddit grouping.
    """
    groups = {
        "🔥 Hot Takes": [],           # Score 70+
        "🤖 Reddit Trending": [],     # High-engagement Reddit posts
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
        is_reddit = article.get("is_reddit", False)
        
        # High score goes to Hot Takes
        if score >= 70:
            groups["🔥 Hot Takes"].append(article)
        # Reddit content with decent scores gets its own category
        elif is_reddit and score >= 40:
            groups["🤖 Reddit Trending"].append(article)
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
        "🔥 Hot Takes", "🤖 Reddit Trending", "🏛️ Political Drama", "💸 Money Fears", 
        "⚠️ Scams & Warnings", "😡 Outrage", "🔪 Crime & Safety",
        "📈 Rates & Economy", "🛡️ Insurance News", "⛈️ Disasters",
        "🏥 Health Scares", "📰 Other"
    ]
    
    result = {}
    for key in priority_order:
        if key in groups and groups[key]:
            result[key] = groups[key]
    
    return result
