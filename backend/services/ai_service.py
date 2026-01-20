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
    
    # Niche-specific context
    niche_context = {
        "Auto Insurance": """
NICHE CONTEXT - AUTO INSURANCE:
- Pain points: High premiums, rate increases, accidents affecting rates, SR-22 requirements
- Desires: Lower rates, easy switching, accident forgiveness, good driver discounts
- Key triggers: Savings amounts, comparison shopping, "15 minutes" convenience
- Audience: Drivers frustrated with current rates, new car buyers, young drivers, seniors""",
        
        "Home Insurance": """
NICHE CONTEXT - HOME INSURANCE:
- Pain points: Rising premiums, coverage gaps, claim denials, natural disaster fears
- Desires: Better coverage, lower rates, bundle discounts, peace of mind
- Key triggers: Home value protection, storm/disaster coverage, family security
- Audience: Homeowners, new home buyers, people in disaster-prone areas""",
        
        "Refi": """
NICHE CONTEXT - REFINANCING:
- Pain points: High monthly payments, high interest rates, debt consolidation needs
- Desires: Lower payments, cash out equity, shorter loan terms, debt freedom
- Key triggers: Interest rate drops, monthly savings amounts, debt payoff
- Audience: Homeowners with equity, people with high-rate mortgages, debt consolidators"""
    }
    
    system_prompt = """You are an elite direct response copywriter specializing in affiliate marketing hooks.
Your hooks are known for:
- Stopping the scroll instantly
- Creating irresistible curiosity
- Tapping into deep emotional triggers
- Feeling native and authentic, not "ad-like"
- Converting browsers into clickers

You write hooks that feel like insider tips from a friend, not corporate advertising."""

    prompt = f"""Generate {num_hooks} scroll-stopping hooks for {niche} affiliate ads.

{niche_context.get(niche, '')}

PROVEN PATTERNS FROM WINNING ADS:{patterns_context if patterns_context else " (No patterns uploaded yet - use your expertise)"}
{news_context if news_context else ""}

{"REQUESTED STYLE: " + hook_style if hook_style else ""}

REQUIREMENTS:
1. Each hook should be 1-2 sentences max
2. Use patterns from winning ads but make them FRESH
3. Incorporate current news angles where relevant
4. Vary the hook types (question, statement, story, stat, etc.)
5. Make them feel native/organic, not "salesy"

Return as JSON array:
[
    {{
        "hook_text": "The actual hook",
        "hook_type": "question/statement/story/stat/curiosity",
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
