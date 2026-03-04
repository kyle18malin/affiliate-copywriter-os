"""
Affiliate Copywriter OS - AI Service
Handles all AI-powered analysis and generation
"""
import json
from typing import Optional
from backend.config import settings

# Initialize AI clients based on configuration
openai_client = None
anthropic_client = None

if settings.openai_api_key:
    from openai import AsyncOpenAI
    openai_client = AsyncOpenAI(api_key=settings.openai_api_key)

if settings.anthropic_api_key:
    from anthropic import AsyncAnthropic
    anthropic_client = AsyncAnthropic(api_key=settings.anthropic_api_key)


async def call_ai(prompt: str, system_prompt: str = None, temperature: float = 0.7) -> str:
    """Call the configured AI provider"""
    
    if settings.ai_provider == "anthropic" and anthropic_client:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            temperature=temperature,
            system=system_prompt or "You are an expert copywriter specializing in affiliate marketing.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    elif openai_client:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            temperature=temperature,
            max_tokens=2000
        )
        return response.choices[0].message.content
    
    else:
        raise ValueError("No AI provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY")


async def analyze_ad(ad_content: str) -> dict:
    """
    Analyze a winning ad and extract universal patterns.
    These patterns can be applied across all niches.
    """
    system_prompt = """You are an expert direct response copywriter and ad analyst. 
Your job is to deconstruct winning ads and extract the universal persuasion patterns that make them effective.
Focus on STRUCTURE and TECHNIQUE, not niche-specific content."""

    prompt = f"""Analyze this winning ad and extract the universal patterns that make it effective:

AD COPY:
{ad_content}

Extract and return as JSON:
{{
    "hook_structure": "Describe the FORMULA/STRUCTURE of the hook (e.g., 'Question + Shocking Stat + Promise')",
    "hook_example": "The actual hook text from the ad",
    "emotional_triggers": ["List the primary emotions this ad triggers"],
    "curiosity_gaps": ["List any curiosity techniques used (open loops, incomplete info, etc.)"],
    "power_words": ["List impactful/persuasive words used"],
    "cta_pattern": "Describe the call-to-action structure",
    "persuasion_techniques": ["List techniques like: scarcity, social proof, authority, fear of loss, etc."]
}}

Return ONLY valid JSON, no other text."""

    response = await call_ai(prompt, system_prompt, temperature=0.3)
    
    # Parse JSON response
    try:
        # Clean up response if needed
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "hook_structure": "Could not parse",
            "hook_example": "",
            "emotional_triggers": [],
            "curiosity_gaps": [],
            "power_words": [],
            "cta_pattern": "",
            "persuasion_techniques": []
        }


async def analyze_news_article(title: str, summary: str) -> dict:
    """
    Analyze a news article for potential ad angles.
    """
    system_prompt = """You are an expert at finding advertising angles in current events.
You specialize in insurance and financial services affiliate marketing."""

    prompt = f"""Analyze this news article for potential advertising angles:

HEADLINE: {title}
SUMMARY: {summary}

Extract angles that could be used for ads in these niches:
- Auto Insurance
- Home Insurance  
- Refinancing (Refi)

Return as JSON:
{{
    "trending_angles": ["List 2-3 ad angles this news could inspire"],
    "emotional_triggers": ["What emotions does this news evoke that ads could leverage?"],
    "relevance_score": 0.0-1.0 (how relevant is this for insurance/finance ads?),
    "hook_ideas": ["2-3 quick hook ideas inspired by this news"]
}}

Return ONLY valid JSON."""

    response = await call_ai(prompt, system_prompt, temperature=0.5)
    
    try:
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except json.JSONDecodeError:
        return {
            "trending_angles": [],
            "emotional_triggers": [],
            "relevance_score": 0.5,
            "hook_ideas": []
        }


async def generate_hooks(
    niche: str,
    pattern_summary: dict,
    recent_news: list[dict],
    num_hooks: int = 5,
    hook_style: str = None
) -> list[dict]:
    """
    Generate hooks combining:
    1. Proven ad patterns (weighted toward niche-specific)
    2. Current news angles
    3. Niche-specific pain points and language
    """
    
    # Build context from patterns
    patterns_context = ""
    if pattern_summary.get("hook_structures"):
        patterns_context += f"\nPROVEN HOOK STRUCTURES:\n" + "\n".join(f"- {s}" for s in pattern_summary["hook_structures"][:10])
    if pattern_summary.get("hook_examples"):
        patterns_context += f"\n\nWINNING HOOK EXAMPLES:\n" + "\n".join(f"- {e}" for e in pattern_summary["hook_examples"][:10])
    if pattern_summary.get("all_emotional_triggers"):
        patterns_context += f"\n\nEFFECTIVE EMOTIONAL TRIGGERS: {', '.join(pattern_summary['all_emotional_triggers'][:15])}"
    if pattern_summary.get("all_power_words"):
        patterns_context += f"\n\nPOWER WORDS THAT WORK: {', '.join(pattern_summary['all_power_words'][:20])}"
    
    # Build news context
    news_context = ""
    if recent_news:
        news_context = "\n\nCURRENT NEWS ANGLES TO LEVERAGE:\n"
        for article in recent_news[:5]:
            news_context += f"- {article.get('title', '')}\n"
            if article.get('trending_angles'):
                news_context += f"  Angles: {', '.join(article['trending_angles'][:2])}\n"
    
    # Niche-specific context - aggressive angles
    niche_context = {
        "Auto Insurance": """
NICHE CONTEXT - AUTO INSURANCE:
- PAIN: Insurance companies are SCREWING drivers with hidden rate hikes. They count on you being too lazy to switch. They profit from your complacency.
- FEAR: One accident = years of premium punishment. Your rate can spike 40%+ for a minor fender bender. The system is rigged against you.
- ANGER: Why are YOU paying more than your neighbor for the same coverage? Why did your rate go up when you had ZERO claims?
- GREED: People are saving $50-100/month by doing this one thing. That's $600-1,200/year you're leaving on the table.
- ENEMY: Big insurance companies, the "loyalty penalty", corporate greed
- AUDIENCE: Anyone who's been screwed by their insurance company (everyone)""",
        
        "Home Insurance": """
NICHE CONTEXT - HOME INSURANCE:
- PAIN: Home insurance rates are SKYROCKETING. Claims getting denied. People left with NOTHING after disasters.
- FEAR: What if a storm destroys your home and your insurance doesn't cover it? What if you're underinsured? What happens to your family?
- ANGER: Insurance companies take your money for years, then fight you when you need them. They find loopholes to deny claims.
- GREED: Some homeowners are paying HALF of what you pay for better coverage. They know something you don't.
- ENEMY: Greedy insurance corporations, claim deniers, coverage gaps you didn't know existed
- AUDIENCE: Homeowners terrified of losing everything, people in disaster-prone areas (hurricanes, floods, fires)""",
        
        "Refi": """
NICHE CONTEXT - REFINANCING:
- PAIN: You're HEMORRHAGING money every month to your mortgage. Your rate is probably too high. You're making your bank rich.
- FEAR: What if rates go up and you miss the window? What if you can't refinance later? Every month you wait = money lost.
- ANGER: Banks want you to keep your high rate. They profit from your inaction. The system doesn't want you to know about this.
- GREED: People are saving $300-500/month by refinancing. That's a car payment. That's a vacation. That's YOUR money.
- ENEMY: Big banks, mortgage companies hoping you stay ignorant, the financial establishment
- AUDIENCE: Homeowners bleeding cash, people who haven't checked rates in 2+ years, debt-stressed families"""
    }
    
    system_prompt = """You are an AGGRESSIVE direct response copywriter trained by the greatest copywriters in history.

YOUR MASTERS' TEACHINGS:
- Eugene Schwartz: Match copy to awareness level. Sophistication matters. Channel existing desire.
- John Caples: Headlines with numbers, "How to", "Warning:", questions that touch self-interest
- Gary Halbert: Write like you talk. AIDA formula. Urgency is mandatory, not optional.
- Dan Kennedy: Fascinations. Proof stacking. Damaging admission. Takeaway selling.
- Robert Cialdini: Scarcity, social proof, authority, reciprocity, commitment, liking
- David Ogilvy: Specifics beat generalities. Headlines with news. Long copy if interesting.
- Joe Sugarman: Slippery slide - each line sells the next. Curiosity triggers. Storytelling bypasses resistance.
- Drew Eric Whitman: Life Force 8 desires - survival, fear, sexual, protection, approval, superiority

YOUR APPROACH:
- BE AGGRESSIVE. Not illegal, but edgy.
- Use FEAR and LOSS AVERSION - what they'll miss is 2x more motivating than what they'll gain
- Create URGENCY - deadlines, scarcity, limited time
- Use CONTROVERSY - take strong stances, call out enemies
- Be SPECIFIC - "37.6% more" beats "much more"
- Pattern interrupt HARD in the first 3 words"""

    prompt = f"""Generate {num_hooks} AGGRESSIVE, scroll-stopping hooks for {niche} affiliate ads.

{niche_context.get(niche, '')}

PROVEN PATTERNS FROM WINNING ADS:{patterns_context if patterns_context else " (No patterns uploaded yet - use your expertise)"}
{news_context if news_context else ""}

{"REQUESTED STYLE: " + hook_style if hook_style else ""}

REQUIREMENTS:
1. Each hook should be 1-2 sentences max (PUNCHY)
2. First 3 words MUST stop the scroll - pattern interrupt
3. Use AGGRESSIVE tactics: fear, greed, controversy, curiosity, anger, shock
4. Include SPECIFIC numbers when possible (not round numbers - 37%, not 40%)
5. Mix these hook types:
   - FEAR/WARNING: "Warning:", "If you do X, you'll lose..."
   - GREED/DESIRE: Specific $ amounts, timeframes, results
   - SHOCK/CONTRARIAN: "Everything you know about X is WRONG"
   - CURIOSITY/OPEN LOOP: Questions that DEMAND answers
   - NEWS JACKING: Tie to current events, political drama, trending topics
6. Make them feel like insider tips, not corporate ads
7. Push boundaries but stay legal

Return as JSON array:
[
    {{
        "hook_text": "The actual hook",
        "hook_type": "fear/greed/shock/curiosity/news/story",
        "emotional_trigger": "Primary emotion targeted",
        "inspiration": "What pattern or news inspired this"
    }}
]

Return ONLY valid JSON array, no other text."""

    response = await call_ai(prompt, system_prompt, temperature=0.8)
    
    try:
        response = response.strip()
        if response.startswith("```"):
            response = response.split("```")[1]
            if response.startswith("json"):
                response = response[4:]
        return json.loads(response)
    except json.JSONDecodeError:
        return []


async def generate_full_ad(
    niche: str,
    hook: str,
    pattern_summary: dict,
    ad_format: str = "native"
) -> str:
    """Generate a full ad from a hook"""
    
    formats = {
        "native": "Native ad style - feels like editorial content, soft sell",
        "direct": "Direct response - clear offer, strong CTA, urgency",
        "story": "Story-based - personal narrative leading to solution",
        "listicle": "Listicle style - numbered points/reasons"
    }
    
    system_prompt = """You are an elite affiliate copywriter. Write ads that convert."""
    
    prompt = f"""Write a full {niche} affiliate ad using this hook:

HOOK: {hook}

FORMAT: {formats.get(ad_format, formats['native'])}

Use these proven patterns:
- Emotional triggers that work: {', '.join(pattern_summary.get('all_emotional_triggers', ['savings', 'security', 'fear of missing out'])[:5])}
- CTA styles that convert: {', '.join(pattern_summary.get('cta_patterns', ['Learn more', 'See if you qualify'])[:3])}

Write the complete ad copy (hook + body + CTA). Keep it concise but compelling."""

    return await call_ai(prompt, system_prompt, temperature=0.7)
