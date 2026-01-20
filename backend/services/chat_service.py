"""
Affiliate Copywriter OS - Chat Service
Conversational AI for script writing and feedback
"""
import json
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


SYSTEM_PROMPT = """You are an elite affiliate copywriter and creative director working inside "Affiliate Copywriter OS".

Your expertise:
- Direct response copywriting
- Video ad scripts (VSLs, UGC scripts, native video ads)
- Hook writing and attention-grabbing openings
- Emotional triggers and persuasion psychology
- Converting cold traffic into clicks
- Writing for niches: Auto Insurance, Home Insurance, Refinancing, and more

Your personality:
- Collaborative and helpful
- Direct and actionable advice
- You explain the "why" behind copy decisions
- You iterate based on feedback without ego
- You balance creativity with proven formulas

When writing scripts or copy:
- Start with a strong hook that stops the scroll
- Use conversational, authentic language (not corporate)
- Include specific pain points and emotional triggers
- Build curiosity and open loops
- End with clear calls-to-action
- Keep it native-feeling, not "salesy"

When given feedback:
- Acknowledge the feedback
- Explain your revisions
- Offer alternatives when relevant

You have access to the user's winning ad library and can reference patterns from their best performers when relevant."""


async def chat_completion(
    messages: list[dict],
    context: dict = None,
    temperature: float = 0.7
) -> str:
    """
    Send a chat completion request with conversation history.
    
    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."}
        context: Optional context about patterns, news, etc.
        temperature: Creativity level
    """
    
    # Build system prompt with context
    system = SYSTEM_PROMPT
    
    if context:
        if context.get("niche"):
            system += f"\n\nCurrent niche focus: {context['niche']}"
        
        if context.get("patterns"):
            patterns = context["patterns"]
            system += "\n\n📊 PATTERNS FROM USER'S WINNING ADS:"
            if patterns.get("hook_examples"):
                system += f"\nHook examples that work: {', '.join(patterns['hook_examples'][:5])}"
            if patterns.get("all_emotional_triggers"):
                system += f"\nEffective emotions: {', '.join(patterns['all_emotional_triggers'][:10])}"
            if patterns.get("all_power_words"):
                system += f"\nPower words: {', '.join(patterns['all_power_words'][:15])}"
        
        if context.get("recent_news"):
            system += "\n\n📰 RECENT NEWS ANGLES:"
            for news in context["recent_news"][:3]:
                system += f"\n- {news}"
    
    # Use Anthropic (Claude) if configured, otherwise OpenAI
    if settings.ai_provider == "anthropic" and anthropic_client:
        response = await anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            temperature=temperature,
            system=system,
            messages=messages
        )
        return response.content[0].text
    
    elif openai_client:
        openai_messages = [{"role": "system", "content": system}]
        openai_messages.extend(messages)
        
        response = await openai_client.chat.completions.create(
            model="gpt-4o",
            messages=openai_messages,
            temperature=temperature,
            max_tokens=4000
        )
        return response.choices[0].message.content
    
    else:
        raise ValueError("No AI provider configured")


async def generate_script(
    script_type: str,
    niche: str,
    topic: str,
    context: dict = None,
    additional_instructions: str = None
) -> str:
    """
    Generate a full script based on type and parameters.
    """
    
    script_prompts = {
        "vsl": f"""Write a Video Sales Letter (VSL) script for {niche}.

Topic/Angle: {topic}

Structure:
1. Pattern interrupt hook (stop the scroll)
2. Problem agitation (make them feel the pain)
3. Story/credibility builder
4. Solution introduction
5. Benefits (not features)
6. Social proof/results
7. Offer presentation
8. Urgency/scarcity
9. Call to action
10. Risk reversal

Keep it conversational and authentic. 2-3 minutes of speaking time.""",

        "ugc": f"""Write a UGC-style (User Generated Content) video script for {niche}.

Topic/Angle: {topic}

Style: Natural, unscripted-feeling, like someone sharing a discovery with a friend
Length: 30-60 seconds
Structure:
1. Attention hook (first 3 seconds are crucial)
2. Personal story/problem
3. Discovery moment
4. Results/transformation
5. Soft CTA

Make it feel authentic, not like an ad.""",

        "native": f"""Write a native ad script for {niche}.

Topic/Angle: {topic}

Style: Editorial, informative, curiosity-driven
Structure:
1. News-style hook
2. Interesting angle/story
3. Problem identification
4. Hint at solution
5. Curiosity-driven CTA

Should feel like content, not advertising.""",

        "hooks": f"""Write 10 scroll-stopping hooks for {niche}.

Topic/Angle: {topic}

Mix of styles:
- Questions that trigger curiosity
- Shocking statistics
- Story openers
- Contrarian statements
- "Did you know" revelations
- Problem callouts
- Result teasers

Each hook should be 1-2 sentences max.""",

        "email": f"""Write a promotional email sequence for {niche}.

Topic/Angle: {topic}

Write 3 emails:
1. Problem/Curiosity (get the open & click)
2. Story/Social Proof (build trust)
3. Urgency/Final CTA (get the conversion)

Keep subject lines punchy. Body copy conversational.""",
    }
    
    prompt = script_prompts.get(script_type, f"Write compelling copy for {niche} about: {topic}")
    
    if additional_instructions:
        prompt += f"\n\nAdditional instructions: {additional_instructions}"
    
    messages = [{"role": "user", "content": prompt}]
    
    return await chat_completion(messages, context, temperature=0.8)
