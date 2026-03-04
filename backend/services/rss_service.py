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
    # ===== MAINSTREAM / GENERAL NEWS =====
    {"name": "Google News - Top Stories", "url": "https://news.google.com/rss", "category": "General"},
    {"name": "Reuters - Top News", "url": "https://feeds.reuters.com/reuters/topNews", "category": "General"},
    {"name": "AP News - Top Stories", "url": "https://rsshub.app/apnews/topics/apf-topnews", "category": "General"},
    {"name": "USA Today - Top Stories", "url": "https://www.usatoday.com/rss/", "category": "General"},
    {"name": "NPR - News", "url": "https://feeds.npr.org/1001/rss.xml", "category": "General"},
    {"name": "ABC News", "url": "https://abcnews.go.com/abcnews/topstories", "category": "General"},
    {"name": "CBS News", "url": "https://www.cbsnews.com/latest/rss/main", "category": "General"},
    {"name": "NBC News", "url": "https://feeds.nbcnews.com/nbcnews/public/news", "category": "General"},
    
    # ===== POLITICAL NEWS - CONSERVATIVE =====
    {"name": "Fox News - Politics", "url": "https://moxie.foxnews.com/google-publisher/politics.xml", "category": "Politics - Right"},
    {"name": "Fox News - US", "url": "https://moxie.foxnews.com/google-publisher/us.xml", "category": "Politics - Right"},
    {"name": "Fox Business", "url": "https://moxie.foxbusiness.com/google-publisher/markets.xml", "category": "Politics - Right"},
    {"name": "New York Post", "url": "https://nypost.com/feed/", "category": "Politics - Right"},
    {"name": "Daily Wire", "url": "https://www.dailywire.com/feeds/rss.xml", "category": "Politics - Right"},
    {"name": "Breitbart", "url": "https://feeds.feedburner.com/breitbart", "category": "Politics - Right"},
    {"name": "Newsmax", "url": "https://www.newsmax.com/rss/Newsfront/1/", "category": "Politics - Right"},
    {"name": "Washington Examiner", "url": "https://www.washingtonexaminer.com/feed", "category": "Politics - Right"},
    {"name": "Daily Caller", "url": "https://dailycaller.com/feed/", "category": "Politics - Right"},
    {"name": "The Federalist", "url": "https://thefederalist.com/feed/", "category": "Politics - Right"},
    
    # ===== POLITICAL NEWS - LIBERAL =====
    {"name": "CNN - Politics", "url": "http://rss.cnn.com/rss/cnn_allpolitics.rss", "category": "Politics - Left"},
    {"name": "CNN - US", "url": "http://rss.cnn.com/rss/cnn_us.rss", "category": "Politics - Left"},
    {"name": "MSNBC - Top Stories", "url": "https://www.msnbc.com/feeds/latest", "category": "Politics - Left"},
    {"name": "New York Times - Politics", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml", "category": "Politics - Left"},
    {"name": "Washington Post - Politics", "url": "https://feeds.washingtonpost.com/rss/politics", "category": "Politics - Left"},
    {"name": "The Hill", "url": "https://thehill.com/feed/", "category": "Politics"},
    {"name": "Politico", "url": "https://www.politico.com/rss/politicopicks.xml", "category": "Politics"},
    {"name": "HuffPost - Politics", "url": "https://www.huffpost.com/section/politics/feed", "category": "Politics - Left"},
    {"name": "Vox", "url": "https://www.vox.com/rss/index.xml", "category": "Politics - Left"},
    {"name": "Slate", "url": "https://slate.com/feeds/all.rss", "category": "Politics - Left"},
    
    # ===== CONTROVERSIAL / OUTRAGE / ATTENTION-GRABBING =====
    {"name": "Daily Mail US", "url": "https://www.dailymail.co.uk/ushome/index.rss", "category": "Tabloid"},
    {"name": "NY Post - News", "url": "https://nypost.com/news/feed/", "category": "Tabloid"},
    {"name": "The Sun US", "url": "https://www.the-sun.com/feed/", "category": "Tabloid"},
    {"name": "TMZ", "url": "https://www.tmz.com/rss.xml", "category": "Celebrity"},
    {"name": "Page Six", "url": "https://pagesix.com/feed/", "category": "Celebrity"},
    
    # ===== ECONOMY / MONEY FEARS =====
    {"name": "CNBC - Top News", "url": "https://www.cnbc.com/id/100003114/device/rss/rss.html", "category": "Finance"},
    {"name": "CNBC - Economy", "url": "https://www.cnbc.com/id/20910258/device/rss/rss.html", "category": "Finance"},
    {"name": "MarketWatch - Top Stories", "url": "https://feeds.marketwatch.com/marketwatch/topstories/", "category": "Finance"},
    {"name": "Bloomberg - Markets", "url": "https://feeds.bloomberg.com/markets/news.rss", "category": "Finance"},
    {"name": "Wall Street Journal", "url": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml", "category": "Finance"},
    {"name": "Yahoo Finance", "url": "https://finance.yahoo.com/news/rssindex", "category": "Finance"},
    {"name": "Business Insider", "url": "https://www.businessinsider.com/rss", "category": "Finance"},
    {"name": "Forbes", "url": "https://www.forbes.com/real-time/feed2/", "category": "Finance"},
    {"name": "Zero Hedge", "url": "https://feeds.feedburner.com/zerohedge/feed", "category": "Finance"},
    
    # ===== CONSUMER OUTRAGE / SCAMS / RIPOFFS =====
    {"name": "Consumer Reports", "url": "https://www.consumerreports.org/rss/", "category": "Consumer"},
    {"name": "Clark Howard", "url": "https://clark.com/feed/", "category": "Consumer"},
    {"name": "Consumerist (via Archive)", "url": "https://consumerist.com/rss.xml", "category": "Consumer"},
    
    # ===== CRIME / SAFETY =====
    {"name": "CNN - Crime", "url": "http://rss.cnn.com/rss/cnn_crime.rss", "category": "Crime"},
    {"name": "Fox News - Crime", "url": "https://moxie.foxnews.com/google-publisher/us.xml", "category": "Crime"},
    {"name": "NY Post - Crime", "url": "https://nypost.com/tag/crime/feed/", "category": "Crime"},
    
    # ===== HEALTH SCARES =====
    {"name": "CNN - Health", "url": "http://rss.cnn.com/rss/cnn_health.rss", "category": "Health"},
    {"name": "WebMD News", "url": "https://rssfeeds.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC", "category": "Health"},
    {"name": "NY Times - Health", "url": "https://rss.nytimes.com/services/xml/rss/nyt/Health.xml", "category": "Health"},
    
    # ===== INSURANCE SPECIFIC =====
    {"name": "Insurance Journal", "url": "https://www.insurancejournal.com/feed/", "category": "Insurance"},
    {"name": "PropertyCasualty360", "url": "https://www.propertycasualty360.com/feed/", "category": "Insurance"},
    {"name": "Insurance News Net", "url": "https://insurancenewsnet.com/feed", "category": "Insurance"},
    
    # ===== REAL ESTATE / MORTGAGE (for Refi) =====
    {"name": "HousingWire", "url": "https://www.housingwire.com/feed/", "category": "Real Estate"},
    {"name": "Mortgage News Daily", "url": "https://www.mortgagenewsdaily.com/rss/", "category": "Mortgage"},
    {"name": "Realtor.com News", "url": "https://www.realtor.com/news/feed/", "category": "Real Estate"},
    {"name": "Zillow Research", "url": "https://www.zillow.com/research/feed/", "category": "Real Estate"},
    
    # ===== CONSUMER FINANCE =====
    {"name": "NerdWallet", "url": "https://www.nerdwallet.com/blog/feed/", "category": "Personal Finance"},
    {"name": "The Penny Hoarder", "url": "https://www.thepennyhoarder.com/feed/", "category": "Personal Finance"},
    {"name": "Bankrate", "url": "https://www.bankrate.com/feed/", "category": "Personal Finance"},
    {"name": "Money", "url": "https://money.com/feed/", "category": "Personal Finance"},
    
    # ===== WEATHER & DISASTERS (Insurance angles) =====
    {"name": "Weather.com - Severe", "url": "https://weather.com/feeds/rss/severe", "category": "Weather"},
    {"name": "AccuWeather - Top Stories", "url": "https://rss.accuweather.com/rss/liveweather_rss.asp?locCode=NAK", "category": "Weather"},
    {"name": "NOAA Climate", "url": "https://www.climate.gov/feeds/all.rss", "category": "Weather"},
    
    # ===== TRENDING / VIRAL =====
    {"name": "BuzzFeed", "url": "https://www.buzzfeed.com/index.xml", "category": "Trending"},
    
    # ═══════════════════════════════════════════════════════════════════
    # REDDIT - THE REAL GOLDMINE (VIRAL, CONTROVERSIAL, EMOTIONAL)
    # ═══════════════════════════════════════════════════════════════════
    
    # ===== VIRAL VIDEO & FREAKOUT CONTENT (Pure engagement gold) =====
    {"name": "Reddit - PublicFreakout", "url": "https://www.reddit.com/r/PublicFreakout/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - facepalm", "url": "https://www.reddit.com/r/facepalm/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - Whatcouldgowrong", "url": "https://www.reddit.com/r/Whatcouldgowrong/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - instant_regret", "url": "https://www.reddit.com/r/instant_regret/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - Wellthatsucks", "url": "https://www.reddit.com/r/Wellthatsucks/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - therewasanattempt", "url": "https://www.reddit.com/r/therewasanattempt/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - AbruptChaos", "url": "https://www.reddit.com/r/AbruptChaos/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - CrazyFuckingVideos", "url": "https://www.reddit.com/r/CrazyFuckingVideos/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - nextfuckinglevel", "url": "https://www.reddit.com/r/nextfuckinglevel/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - Damnthatsinteresting", "url": "https://www.reddit.com/r/Damnthatsinteresting/top/.rss?t=day", "category": "Reddit - Viral"},
    
    # ===== JUSTICE / REVENGE / KARMA (Satisfying emotional content) =====
    {"name": "Reddit - JusticeServed", "url": "https://www.reddit.com/r/JusticeServed/top/.rss?t=day", "category": "Reddit - Justice"},
    {"name": "Reddit - MaliciousCompliance", "url": "https://www.reddit.com/r/MaliciousCompliance/top/.rss?t=day", "category": "Reddit - Justice"},
    {"name": "Reddit - pettyrevenge", "url": "https://www.reddit.com/r/pettyrevenge/top/.rss?t=day", "category": "Reddit - Justice"},
    {"name": "Reddit - ProRevenge", "url": "https://www.reddit.com/r/ProRevenge/top/.rss?t=week", "category": "Reddit - Justice"},
    {"name": "Reddit - NuclearRevenge", "url": "https://www.reddit.com/r/NuclearRevenge/top/.rss?t=week", "category": "Reddit - Justice"},
    {"name": "Reddit - LeopardsAteMyFace", "url": "https://www.reddit.com/r/LeopardsAteMyFace/top/.rss?t=day", "category": "Reddit - Justice"},
    {"name": "Reddit - byebyejob", "url": "https://www.reddit.com/r/byebyejob/top/.rss?t=day", "category": "Reddit - Justice"},
    {"name": "Reddit - FUCKYOUINPARTICULAR", "url": "https://www.reddit.com/r/FUCKYOUINPARTICULAR/top/.rss?t=day", "category": "Reddit - Justice"},
    
    # ===== ENTITLED PEOPLE / CHOOSING BEGGARS (Outrage content) =====
    {"name": "Reddit - ChoosingBeggars", "url": "https://www.reddit.com/r/ChoosingBeggars/top/.rss?t=day", "category": "Reddit - Entitled"},
    {"name": "Reddit - EntitledParents", "url": "https://www.reddit.com/r/entitledparents/top/.rss?t=day", "category": "Reddit - Entitled"},
    {"name": "Reddit - EntitledPeople", "url": "https://www.reddit.com/r/EntitledPeople/top/.rss?t=day", "category": "Reddit - Entitled"},
    {"name": "Reddit - FuckYouKaren", "url": "https://www.reddit.com/r/FuckYouKaren/top/.rss?t=day", "category": "Reddit - Entitled"},
    {"name": "Reddit - IDontWorkHereLady", "url": "https://www.reddit.com/r/IDontWorkHereLady/top/.rss?t=day", "category": "Reddit - Entitled"},
    
    # ===== CAR CRASHES / BAD DRIVERS (Auto insurance GOLD) =====
    {"name": "Reddit - IdiotsInCars", "url": "https://www.reddit.com/r/IdiotsInCars/top/.rss?t=day", "category": "Reddit - Cars"},
    {"name": "Reddit - Dashcam", "url": "https://www.reddit.com/r/Dashcam/top/.rss?t=day", "category": "Reddit - Cars"},
    {"name": "Reddit - CarCrash", "url": "https://www.reddit.com/r/CarCrash/top/.rss?t=week", "category": "Reddit - Cars"},
    {"name": "Reddit - Roadcam", "url": "https://www.reddit.com/r/Roadcam/top/.rss?t=day", "category": "Reddit - Cars"},
    {"name": "Reddit - BadDrivers", "url": "https://www.reddit.com/r/BadDrivers/top/.rss?t=week", "category": "Reddit - Cars"},
    
    # ===== CONFESSIONS / F*CK UPS / DRAMA (Raw emotional stories) =====
    {"name": "Reddit - tifu", "url": "https://www.reddit.com/r/tifu/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - confessions", "url": "https://www.reddit.com/r/confessions/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - TrueOffMyChest", "url": "https://www.reddit.com/r/TrueOffMyChest/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - AmItheAsshole", "url": "https://www.reddit.com/r/AmItheAsshole/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - relationship_advice", "url": "https://www.reddit.com/r/relationship_advice/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - BestofRedditorUpdates", "url": "https://www.reddit.com/r/BestofRedditorUpdates/top/.rss?t=day", "category": "Reddit - Stories"},
    {"name": "Reddit - offmychest", "url": "https://www.reddit.com/r/offmychest/top/.rss?t=day", "category": "Reddit - Stories"},
    
    # ===== CORPORATE HATE / DYSTOPIA (Anti-establishment rage) =====
    {"name": "Reddit - antiwork", "url": "https://www.reddit.com/r/antiwork/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - WorkReform", "url": "https://www.reddit.com/r/WorkReform/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - LateStageCapitalism", "url": "https://www.reddit.com/r/LateStageCapitalism/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - ABoringDystopia", "url": "https://www.reddit.com/r/ABoringDystopia/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - lostgeneration", "url": "https://www.reddit.com/r/lostgeneration/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - recruitinghell", "url": "https://www.reddit.com/r/recruitinghell/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - assholedesign", "url": "https://www.reddit.com/r/assholedesign/top/.rss?t=day", "category": "Reddit - Corporate"},
    {"name": "Reddit - HailCorporate", "url": "https://www.reddit.com/r/HailCorporate/top/.rss?t=day", "category": "Reddit - Corporate"},
    
    # ===== MONEY DISASTERS / FINANCIAL FEAR =====
    {"name": "Reddit - wallstreetbets", "url": "https://www.reddit.com/r/wallstreetbets/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - povertyfinance", "url": "https://www.reddit.com/r/povertyfinance/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - personalfinance", "url": "https://www.reddit.com/r/personalfinance/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - StudentLoans", "url": "https://www.reddit.com/r/StudentLoans/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - Debt", "url": "https://www.reddit.com/r/debt/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - FluentInFinance", "url": "https://www.reddit.com/r/FluentInFinance/top/.rss?t=day", "category": "Reddit - Money"},
    {"name": "Reddit - economy", "url": "https://www.reddit.com/r/economy/top/.rss?t=day", "category": "Reddit - Money"},
    
    # ===== HOUSING CRISIS / REAL ESTATE DRAMA =====
    {"name": "Reddit - REBubble", "url": "https://www.reddit.com/r/REBubble/top/.rss?t=day", "category": "Reddit - Housing"},
    {"name": "Reddit - RealEstate", "url": "https://www.reddit.com/r/RealEstate/top/.rss?t=day", "category": "Reddit - Housing"},
    {"name": "Reddit - FirstTimeHomeBuyer", "url": "https://www.reddit.com/r/FirstTimeHomeBuyer/top/.rss?t=day", "category": "Reddit - Housing"},
    {"name": "Reddit - homeowners", "url": "https://www.reddit.com/r/homeowners/top/.rss?t=day", "category": "Reddit - Housing"},
    {"name": "Reddit - Landlord", "url": "https://www.reddit.com/r/Landlord/top/.rss?t=week", "category": "Reddit - Housing"},
    
    # ===== SCAMS / FRAUD / WARNINGS =====
    {"name": "Reddit - Scams", "url": "https://www.reddit.com/r/Scams/top/.rss?t=day", "category": "Reddit - Scams"},
    {"name": "Reddit - ScamHomeWarranty", "url": "https://www.reddit.com/r/ScamHomeWarranty/top/.rss?t=week", "category": "Reddit - Scams"},
    {"name": "Reddit - Insurance", "url": "https://www.reddit.com/r/Insurance/top/.rss?t=week", "category": "Reddit - Insurance"},
    {"name": "Reddit - HealthInsurance", "url": "https://www.reddit.com/r/HealthInsurance/top/.rss?t=week", "category": "Reddit - Insurance"},
    
    # ===== ABSURD NEWS / NOTTHEONION (Headlines that write themselves) =====
    {"name": "Reddit - nottheonion", "url": "https://www.reddit.com/r/nottheonion/top/.rss?t=day", "category": "Reddit - News"},
    {"name": "Reddit - news", "url": "https://www.reddit.com/r/news/top/.rss?t=day", "category": "Reddit - News"},
    {"name": "Reddit - worldnews", "url": "https://www.reddit.com/r/worldnews/top/.rss?t=day", "category": "Reddit - News"},
    {"name": "Reddit - politics", "url": "https://www.reddit.com/r/politics/top/.rss?t=day", "category": "Reddit - News"},
    {"name": "Reddit - Conservative", "url": "https://www.reddit.com/r/Conservative/top/.rss?t=day", "category": "Reddit - News"},
    
    # ===== CONTROVERSY / DRAMA / OPINIONS =====
    {"name": "Reddit - unpopularopinion", "url": "https://www.reddit.com/r/unpopularopinion/top/.rss?t=day", "category": "Reddit - Controversy"},
    {"name": "Reddit - The10thDentist", "url": "https://www.reddit.com/r/The10thDentist/top/.rss?t=day", "category": "Reddit - Controversy"},
    {"name": "Reddit - SubredditDrama", "url": "https://www.reddit.com/r/SubredditDrama/top/.rss?t=day", "category": "Reddit - Controversy"},
    {"name": "Reddit - OutOfTheLoop", "url": "https://www.reddit.com/r/OutOfTheLoop/top/.rss?t=day", "category": "Reddit - Controversy"},
    {"name": "Reddit - HobbyDrama", "url": "https://www.reddit.com/r/HobbyDrama/top/.rss?t=week", "category": "Reddit - Controversy"},
    {"name": "Reddit - agedlikemilk", "url": "https://www.reddit.com/r/agedlikemilk/top/.rss?t=day", "category": "Reddit - Controversy"},
    
    # ===== INFURIATING / RAGE CONTENT =====
    {"name": "Reddit - mildlyinfuriating", "url": "https://www.reddit.com/r/mildlyinfuriating/top/.rss?t=day", "category": "Reddit - Rage"},
    {"name": "Reddit - extremelyinfuriating", "url": "https://www.reddit.com/r/extremelyinfuriating/top/.rss?t=day", "category": "Reddit - Rage"},
    {"name": "Reddit - rage", "url": "https://www.reddit.com/r/rage/top/.rss?t=day", "category": "Reddit - Rage"},
    {"name": "Reddit - iamatotalpieceofshit", "url": "https://www.reddit.com/r/iamatotalpieceofshit/top/.rss?t=day", "category": "Reddit - Rage"},
    {"name": "Reddit - trashy", "url": "https://www.reddit.com/r/trashy/top/.rss?t=day", "category": "Reddit - Rage"},
    
    # ===== LEGAL DRAMA / NIGHTMARE STORIES =====
    {"name": "Reddit - legaladvice", "url": "https://www.reddit.com/r/legaladvice/top/.rss?t=day", "category": "Reddit - Legal"},
    {"name": "Reddit - bestoflegaladvice", "url": "https://www.reddit.com/r/bestoflegaladvice/top/.rss?t=day", "category": "Reddit - Legal"},
    
    # ===== CRINGE / VIRAL SOCIAL CONTENT =====
    {"name": "Reddit - TikTokCringe", "url": "https://www.reddit.com/r/TikTokCringe/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - cringepics", "url": "https://www.reddit.com/r/cringepics/top/.rss?t=day", "category": "Reddit - Viral"},
    {"name": "Reddit - sadcringe", "url": "https://www.reddit.com/r/sadcringe/top/.rss?t=day", "category": "Reddit - Viral"},
    
    # ===== POPULAR / ALL (Catch-all viral) =====
    {"name": "Reddit - popular", "url": "https://www.reddit.com/r/popular/top/.rss?t=day", "category": "Reddit - Trending"},
    {"name": "Reddit - all", "url": "https://www.reddit.com/r/all/top/.rss?t=day", "category": "Reddit - Trending"},
    
    # ===== GOOGLE NEWS SPECIFIC TOPICS =====
    {"name": "Google News - Business", "url": "https://news.google.com/rss/topics/CAAqJggKIiBDQkFTRWdvSUwyMHZNRGx6TVdZU0FtVnVHZ0pWVXlnQVAB", "category": "Finance"},
    {"name": "Google News - Economy", "url": "https://news.google.com/rss/search?q=economy+OR+inflation+OR+recession", "category": "Finance"},
    {"name": "Google News - Insurance", "url": "https://news.google.com/rss/search?q=insurance+rates+OR+insurance+prices", "category": "Insurance"},
    {"name": "Google News - Trump", "url": "https://news.google.com/rss/search?q=trump", "category": "Politics"},
    {"name": "Google News - Congress", "url": "https://news.google.com/rss/search?q=congress+OR+senate+OR+bill+passed", "category": "Politics"},
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


async def search_articles(db: AsyncSession, keyword: str, limit: int = 100) -> list[NewsArticle]:
    """Search articles by keyword in title or summary"""
    from sqlalchemy import or_
    
    search_term = f"%{keyword.lower()}%"
    result = await db.execute(
        select(NewsArticle)
        .options(selectinload(NewsArticle.feed))
        .where(
            or_(
                NewsArticle.title.ilike(search_term),
                NewsArticle.summary.ilike(search_term)
            )
        )
        .order_by(NewsArticle.fetched_at.desc())
        .limit(limit)
    )
    return list(result.scalars().all())
