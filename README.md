# Affiliate Copywriter OS

AI-powered hook generation for affiliate marketing campaigns. Combines trending news with proven ad patterns to generate scroll-stopping copy.

![Dashboard Preview](https://via.placeholder.com/800x400?text=Affiliate+Copywriter+OS)

## Features

- 🎯 **Niche-Specific Generation** - Pre-configured for Auto Insurance, Home Insurance, and Refi
- 📰 **RSS News Aggregation** - Pulls from multiple news sources automatically
- 📝 **Ad Library** - Upload and analyze your winning ads
- 🧠 **Pattern Extraction** - AI extracts universal patterns from your best performers
- ⚡ **Hook Generation** - Combines news trends + ad patterns for fresh hooks
- 🎨 **Beautiful Dashboard** - Dark themed, modern UI

## How It Works

```
┌─────────────────┐     ┌─────────────────┐
│   RSS Feeds     │     │  Winning Ads    │
│  (News Sources) │     │  (Your Swipes)  │
└────────┬────────┘     └────────┬────────┘
         │                       │
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Trending Angles │     │ Pattern Extract │
│ + Emotions      │     │ (Universal)     │
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │   AI Hook Generator   │
         │ (Niche-weighted)      │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │  Generated Hooks      │
         │  Ready for Ads!       │
         └───────────────────────┘
```

## Quick Start

### 1. Set Up Environment

```bash
# Clone and enter directory
cd "Creative Idea Generator"

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

Create a `.env` file in the root directory:

```env
# Choose one or both AI providers
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Which provider to use: "openai" or "anthropic"
AI_PROVIDER=openai
```

### 3. Start the Backend

```bash
python run.py
```

The API will be available at `http://localhost:8000`

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

The dashboard will be available at `http://localhost:5173`

## Usage

### 1. Fetch News
Click "Fetch Latest News" on the dashboard to pull articles from all RSS feeds.

### 2. Analyze News (Optional)
Click "Analyze" on any article to extract trending angles and emotions.

### 3. Upload Winning Ads
Go to the Ads tab and upload your best-performing ads. Optionally tag them to a specific niche for priority weighting.

### 4. Extract Patterns
Click "Extract Patterns" on any ad to have AI analyze the hook structure, emotional triggers, power words, etc.

### 5. Generate Hooks
Go to the Generate tab, select a niche, and click "Generate Hooks". The AI will combine:
- Patterns from your winning ads (niche-specific prioritized)
- Trending news angles
- Niche-specific pain points and language

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/niches` | GET | List all niches |
| `/api/feeds` | GET/POST | Manage RSS feeds |
| `/api/feeds/fetch` | POST | Fetch news from all feeds |
| `/api/news` | GET | List news articles |
| `/api/news/{id}/analyze` | POST | Analyze article for ad angles |
| `/api/ads` | GET/POST | Manage ads |
| `/api/ads/{id}/analyze` | POST | Extract patterns from ad |
| `/api/generate/hooks` | POST | Generate hooks for a niche |
| `/api/generate/full-ad` | POST | Generate full ad from hook |
| `/api/stats` | GET | Dashboard statistics |

## Pre-configured Niches

- **Auto Insurance** - Pain points around high premiums, rate increases, easy switching
- **Home Insurance** - Coverage gaps, natural disasters, bundle discounts
- **Refi** - Monthly payment reduction, equity access, debt consolidation

## Pre-configured RSS Feeds

- Google News, Reuters, CNBC, Bloomberg
- Insurance Journal, PropertyCasualty360
- HousingWire, Mortgage News Daily
- NerdWallet, The Penny Hoarder
- And more...

## Tech Stack

- **Backend**: Python, FastAPI, SQLAlchemy, SQLite
- **AI**: OpenAI GPT-4o / Anthropic Claude
- **Frontend**: React, Vite, Tailwind CSS
- **RSS Parsing**: feedparser, httpx

## Adding Custom Niches

```python
# Via API
POST /api/niches
{
    "name": "Health & Wellness",
    "description": "Supplements, fitness, weight loss"
}
```

Or add to `backend/config.py`:
```python
default_niches: list[str] = ["Auto Insurance", "Home Insurance", "Refi", "Health & Wellness"]
```

## License

MIT
