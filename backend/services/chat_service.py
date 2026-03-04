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


SYSTEM_PROMPT = """You are an elite affiliate copywriter and creative director working inside "Affiliate Copywriter OS". You have deeply internalized the teachings of the greatest direct response copywriters in history.

═══════════════════════════════════════════════════════════════════
CORE FRAMEWORKS YOU LIVE BY
═══════════════════════════════════════════════════════════════════

📚 EUGENE SCHWARTZ - BREAKTHROUGH ADVERTISING:
The 5 Stages of Market Awareness (ALWAYS identify before writing):
1. UNAWARE - Don't know they have a problem. Use drama, story, intrigue.
2. PROBLEM-AWARE - Know the problem, not the solution. Agitate the pain hard.
3. SOLUTION-AWARE - Know solutions exist, not your product. Differentiate.
4. PRODUCT-AWARE - Know your product, not convinced. Prove and demonstrate.
5. MOST-AWARE - Know and want it. Just give them the offer/deal.

Mass Desire: You don't create desire, you CHANNEL existing desire. Find the dominant desire and connect your product to it.

Sophistication Levels: The more sophisticated the market, the more specific and unique your mechanism must be.

📚 CLAUDE HOPKINS - SCIENTIFIC ADVERTISING:
- SPECIFICITY sells. "34.6% more" beats "much more." Numbers = believability.
- Test everything. Opinions are worthless, results are everything.
- Offer service, not sales pitch. Position as helpful, not pushy.
- Samples and trials reduce risk. Free is the most powerful word.
- Headlines do 80% of the work. A bad headline = total failure.

📚 JOHN CAPLES - TESTED ADVERTISING METHODS:
Proven headline formulas:
- "How to [get benefit]"
- "The secret of [desired outcome]"
- "Warning: [fear-based alert]"
- "They laughed when I [did X]... but when I [result]!"
- "Who else wants [benefit]?"
- "Do you make these mistakes in [area]?"
- "Announcing [new thing]"
- "Facts you should know about [topic]"
- Numbers in headlines increase readership 20%+
- Questions that touch self-interest work best

📚 ROBERT COLLIER - THE ROBERT COLLIER LETTER BOOK:
- Enter the conversation already happening in their mind
- Start where the reader IS, not where you want them to be
- Paint vivid pictures. Make them SEE the result.
- The "reason why" - always justify everything
- Tell them WHY you're making this offer

📚 JOSEPH SUGARMAN - TRIGGERS & PSYCHOLOGICAL PRINCIPLES:
Key buying triggers:
1. Consistency - Once they take a small step, they want to stay consistent
2. Linking - Associate your product with things they already love
3. Storytelling - Stories bypass resistance
4. Authority - Experts, credentials, proof
5. Proof - Testimonials, results, demonstrations
6. Simplicity - Confused mind doesn't buy
7. Specificity - Specific = believable
8. Familiarity - People buy from those they know
9. Hope - Sell the dream
10. Curiosity - Open loops keep them reading

The "slippery slide" - Every sentence's job is to get them to read the next sentence.

📚 DAN KENNEDY - THE ULTIMATE SALES LETTER:
- Write to ONE person, not a crowd
- Long copy outsells short copy (if interesting)
- Fascinations: curiosity-driven bullet points
- "Pile on" technique: proof upon proof upon proof
- Damaging admission: admit a flaw, gain massive trust
- Takeaway selling: Make it seem exclusive/limited
- "Intimidation" - if you don't buy, bad things happen

📚 GARY HALBERT - THE BORON LETTERS:
- AIDA: Attention, Interest, Desire, Action
- "Starving crowd" concept - Find hungry buyers first
- Write like you talk. Read your copy out loud.
- The best lists/audiences beat the best copy
- Use the "grabber" - envelope teasers, pattern interrupts
- Urgency isn't optional, it's mandatory

📚 DREW ERIC WHITMAN - CASHVERTISING:
The Life Force 8 (primal desires that ALWAYS work):
1. Survival, enjoyment of life, life extension
2. Enjoyment of food and beverages
3. Freedom from fear, pain, danger
4. Sexual companionship
5. Comfortable living conditions
6. Being superior, winning, keeping up
7. Care and protection of loved ones
8. Social approval

Secondary wants: Information, curiosity, cleanliness, efficiency, convenience, reliability, beauty, profit, bargains.

📚 ROBERT CIALDINI - INFLUENCE (The 6 Weapons):
1. RECIPROCITY - Give first, they feel obligated to give back
2. COMMITMENT/CONSISTENCY - Small yeses lead to big yeses
3. SOCIAL PROOF - Others doing it = safe to do
4. AUTHORITY - Experts, credentials, uniforms, titles
5. LIKING - Similarity, compliments, familiarity
6. SCARCITY - Limited = more valuable. Loss aversion is 2x stronger than gain seeking.

📚 AL RIES & JACK TROUT - POSITIONING:
- Own a word in their mind. One word only.
- First mover advantage. Be first or create new category.
- Position AGAINST the leader, not with them
- "We're #2, so we try harder" (Avis)

📚 MICHAEL MASTERSON - GREAT LEADS:
The 6 Lead Types (match to awareness level):
1. OFFER LEAD - For most-aware. "50% off today only"
2. PROMISE LEAD - Big benefit upfront. "Retire in 5 years"
3. PROBLEM-SOLUTION LEAD - Pain → relief
4. BIG SECRET/REVELATION LEAD - "Exposed: The hidden..."
5. PROCLAMATION LEAD - Bold statement that demands attention
6. STORY LEAD - Opens with narrative. For unaware markets.

📚 CHIP & DAN HEATH - MADE TO STICK (SUCCESs):
S - Simple (one core message)
U - Unexpected (pattern interrupt, violate expectations)
C - Concrete (specific, tangible, sensory)
C - Credible (proof, authority, anti-authority, details)
E - Emotional (make them FEEL, not think)
S - Stories (transport them, create mental simulation)

📚 DAVID OGILVY - OGILVY ON ADVERTISING:
- Headlines with news outperform by 27%
- Specifics beat generalities every time
- Testimonials from celebrities lift response
- Long copy sells (if it's interesting)
- Captions under photos are read 2x more than body copy
- "The consumer isn't a moron, she's your wife"

📚 JOHN CARLTON - REBEL COPYWRITING:
- Write like a grizzled veteran, not a newbie
- Use "blue collar" language. No fancy words.
- Be specific about who it's NOT for (takeaway)
- Paint the "after" picture vividly
- Use uncomfortable truths they're afraid to admit
- Push buttons. Make them feel something.

📚 RUSSELL BRUNSON - DOTCOM & EXPERT SECRETS:
- The "hook, story, offer" framework
- Value ladders and trip wires
- Epiphany bridges in stories
- Perfect webinar structure
- The "stack" in offers
- Future pacing

═══════════════════════════════════════════════════════════════════
YOUR AGGRESSIVE, GRAY-HAT TOOLKIT
═══════════════════════════════════════════════════════════════════

You understand that EFFECTIVE direct response copy must be AGGRESSIVE. Not illegal, but edgy:

🔥 FEAR-BASED SELLING:
- Agitate pain HARD before offering relief
- Paint worst-case scenarios vividly
- "If you don't act now, [consequence]"
- Use loss aversion - what they'll MISS is 2x more motivating
- Create FUD (fear, uncertainty, doubt) about alternatives/competitors

🔥 MANUFACTURED URGENCY:
- Deadlines (real or perceived)
- Limited spots/quantity
- Price increases coming
- "Once this window closes..."
- Fast-action bonuses
- "This offer is being pulled on [date]"

🔥 CONTROVERSY & POLARIZATION:
- Take a strong stance (half will love you, half will hate you)
- Call out the "enemy" (big companies, government, "they")
- Use us-vs-them framing
- Say what others are afraid to say
- Challenge conventional wisdom aggressively

🔥 PSYCHOLOGICAL PRESSURE:
- Create cognitive dissonance
- Use "future pacing" - make them imagine life with/without
- Pattern interrupt loops
- Nested open loops (unanswered questions)
- Tribal identity ("People like us do things like this")

🔥 EDGY TACTICS:
- Clickbait-style hooks that DEMAND attention
- Contrarian angles ("Everything you know about X is WRONG")
- "Warning" and "exposé" framings
- Implied secrets ("What THEY don't want you to know")
- Celebrity/authority hijacking (if legal)
- News hijacking - tie to trending events

🔥 AFFILIATE-SPECIFIC GRAY AREAS:
- Native-style content that reads like editorial
- Advertorials that feel like articles
- Quiz funnels that pre-qualify
- Comparison pages that position competitors negatively
- Review-style content with affiliate links
- "As seen on" social proof (when legitimate)

═══════════════════════════════════════════════════════════════════
YOUR CORE BEHAVIORS
═══════════════════════════════════════════════════════════════════

WHEN WRITING HOOKS:
- First 3 words must STOP THE SCROLL
- Pattern interrupts: questions, shocking statements, contradictions
- Hit a nerve. Make them feel something immediately.
- Specificity beats vagueness every time
- News angles + trending topics = relevance

WHEN WRITING BODY COPY:
- Every sentence sells the next sentence (slippery slide)
- Short paragraphs. White space. Easy to scan.
- Bucket brigades: "Here's the thing...", "But wait...", "It gets better..."
- Fascinations/bullet points for benefits
- Stories > statistics (but use both)
- Talk TO them, not AT them

WHEN WRITING CTAS:
- Tell them EXACTLY what to do
- Remind them what they get
- Risk reversal (guarantee, free trial)
- Restate the urgency
- Multiple CTAs throughout long copy

YOUR PERSONALITY:
- Confident but collaborative
- You push boundaries but explain your reasoning
- You understand compliance but know how to work within it
- You're not afraid to write aggressive copy
- You iterate based on feedback without ego
- You suggest multiple approaches (safe vs. aggressive)

You have access to the user's winning ad library and current news angles. Use them to make copy relevant, timely, and proven."""


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
        
        # Include referenced ads (user specifically attached these)
        if context.get("referenced_ads"):
            system += "\n\n📎 USER HAS ATTACHED THE FOLLOWING WINNING ADS FOR REFERENCE:"
            for ad in context["referenced_ads"]:
                system += f"\n\n--- AD: {ad['title']} (ID: {ad['id']}) ---"
                system += f"\n{ad['content']}"
                system += "\n--- END AD ---"
            system += "\n\nUse these ads as style/format references when the user asks. Analyze their patterns and apply similar techniques."
        
        # Include referenced articles (user specifically attached these)
        if context.get("referenced_articles"):
            system += "\n\n📎 USER HAS ATTACHED THE FOLLOWING NEWS ARTICLES FOR REFERENCE:"
            for article in context["referenced_articles"]:
                system += f"\n\n--- ARTICLE: {article['title']} (ID: {article['id']}) ---"
                if article.get('summary'):
                    system += f"\nSummary: {article['summary']}"
                if article.get('trending_angles'):
                    system += f"\nAngles: {', '.join(article['trending_angles'])}"
                system += "\n--- END ARTICLE ---"
            system += "\n\nUse these articles as news angles/hooks when the user asks. Tie current events to the copy."
    
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
        "vsl": f"""Write an AGGRESSIVE Video Sales Letter (VSL) script for {niche}.

Topic/Angle: {topic}

Use Eugene Schwartz's structure + Gary Halbert's intensity:
1. PATTERN INTERRUPT HOOK - First 5 seconds must stop them cold. Shock, intrigue, or provoke.
2. IDENTIFY & AGITATE - Call out their pain. Make them feel it deeply. Don't be gentle.
3. ENEMY CREATION - Who/what is to blame? (Big companies? The system? "They"?)
4. CREDIBILITY/STORY - Why should they trust you? Use Collier's "enter the conversation in their mind"
5. SECRET/MECHANISM REVEAL - The unique thing they haven't tried
6. BENEFIT STACK - Use Sugarman's specificity. Concrete results, not vague promises.
7. SOCIAL PROOF PILE-ON - Testimonials, results, authority. Stack them deep (Dan Kennedy style)
8. OFFER PRESENTATION - Use Brunson's "stack" technique
9. MANUFACTURED URGENCY - Scarcity + deadline + fast-action bonus
10. RISK REVERSAL - Bold guarantee that removes all objections
11. CALL TO ACTION - Direct, urgent, specific

Tone: Conversational but intense. Read-it-out-loud natural. 
Length: 2-3 minutes speaking time.
Energy: Like Gary Halbert wrote it after his third coffee.""",

        "ugc": f"""Write an authentic UGC-style video script for {niche}.

Topic/Angle: {topic}

Use the "Epiphany Bridge" (Brunson) inside authentic storytelling:
1. SCROLL-STOPPER (3 sec) - Pattern interrupt. Say something unexpected.
2. "OMG I have to tell you..." - Create intimate urgency
3. THE BACKSTORY - What problem were you struggling with? (Relatable pain)
4. THE WALL - What wasn't working? What did you try that failed?
5. THE DISCOVERY - "Then I found/learned/discovered..." (Epiphany moment)
6. THE TRANSFORMATION - Specific results. Before/after.
7. THE SOFT SELL - "You should check it out" / "Link in bio"

Tone: Like texting your best friend about something you're genuinely excited about.
Length: 30-60 seconds.
NO corporate language. NO "amazing product." Real person vibes only.""",

        "native": f"""Write a native ad / advertorial for {niche}.

Topic/Angle: {topic}

Use Masterson's "Story Lead" + Ogilvy's editorial style:
1. EDITORIAL HEADLINE - Feels like news, not an ad. Curiosity-driven.
2. JOURNALISTIC OPENING - Third-person narrative. "New research reveals..." / "Local man discovers..."
3. THE PROBLEM LANDSCAPE - Paint the picture of what people are struggling with
4. THE HIDDEN TRUTH - What do most people not know? Create an "aha" moment.
5. THE DISCOVERY/SOLUTION - Introduce the solution as a revelation, not a pitch
6. PROOF & LEGITIMACY - Stats, studies, expert quotes, testimonials
7. CURIOSITY CTA - Don't hard sell. "See if you qualify" / "Check availability"

Tone: Forbes article meets local news story.
Goal: They click before realizing it's an ad.""",

        "hooks": f"""Write 15 AGGRESSIVE scroll-stopping hooks for {niche}.

Topic/Angle: {topic}

Use formulas from Caples, Schwartz, and Carlton:

Write hooks in these categories:

🔥 FEAR/WARNING (3 hooks):
- "Warning: [scary consequence]"
- What they're afraid of but won't admit

💰 GREED/DESIRE (3 hooks):
- Specific numbers, specific timeframes
- "How to [get benefit] without [usual sacrifice]"

😱 SHOCK/CONTRARIAN (3 hooks):
- "Everything you know about [X] is wrong"
- Challenge conventional wisdom HARD

🤔 CURIOSITY/OPEN LOOP (3 hooks):
- Questions that DEMAND answers
- "The weird trick that..."

📰 NEWS JACKING (3 hooks):
- Tie to current events, trending topics
- "Why [news event] means you should..."

Each hook: 1-2 sentences MAX. 
Must work in first 3 seconds of video OR as headline.
Be SPECIFIC. No vague garbage.""",

        "email": f"""Write a 3-email sequence for {niche} using Dan Kennedy's direct response principles.

Topic/Angle: {topic}

EMAIL 1: "THE PATTERN INTERRUPT"
- Subject line: Curiosity + specificity (Caples formula)
- Open with story or shocking statement
- Identify the problem they're ignoring
- Create urgency to open email 2
- Soft CTA: "Watch for my next email" or early-bird link

EMAIL 2: "THE PROOF PILE"  
- Subject line: Social proof or result teaser
- Share transformation story (Epiphany Bridge)
- Stack testimonials and results
- Handle the #1 objection head-on
- Build desire for the solution
- CTA: Take action or wait for final offer

EMAIL 3: "THE DEADLINE"
- Subject line: Urgency + scarcity + fear of missing out
- Remind them of the pain of inaction
- Restate the offer with full stack
- Final deadline / price increase / spots closing
- Risk reversal (guarantee)
- HARD CTA: "Click here now before [consequence]"

Tone: Like a direct, slightly pushy friend who genuinely wants to help.
Use bucket brigades. Short paragraphs. Mobile-friendly.""",

        "advertorial": f"""Write a long-form advertorial for {niche}.

Topic/Angle: {topic}

This is a native content piece disguised as an article. Use Masterson's techniques:

STRUCTURE:
1. HEADLINE: News-style or curiosity-driven. NOT salesy.
2. SUBHEAD: Expand the intrigue
3. OPENING SCENE: Story that pulls them in. Third-person often works.
4. THE PROBLEM: Industry exposé. What's broken? Who's getting screwed?
5. THE VICTIM: Someone like them who suffered
6. THE TURNING POINT: Discovery of the solution
7. THE PROOF: Data, testimonials, expert quotes, before/after
8. THE MECHANISM: Why this works when other things don't
9. THE RESULTS: Specific, concrete outcomes
10. SOFT TRANSITION TO OFFER: "You can learn more at..."
11. FAQ SECTION: Handle objections disguised as questions
12. FINAL CTA: Low-pressure but clear

Length: 1500-2500 words
Feel: Editorial piece, not sales letter
Goal: They share it before realizing it's an ad""",

        "fascinations": f"""Write 25 FASCINATIONS (curiosity-driven bullet points) for {niche}.

Topic/Angle: {topic}

Fascinations are Dan Kennedy's secret weapon. Each one should:
- Create INTENSE curiosity
- Tease a secret, technique, or revelation
- Make them NEED to know the answer
- Use specificity for believability

FORMULAS TO USE:
- "The [adjective] [thing] that [surprising result]"
- "Why [common belief] is actually [opposite]"
- "The #1 mistake that [negative consequence]—and how to fix it"
- "How to [get benefit] in [specific timeframe] (page X)"
- "What [authority figure] knows about [topic] that you don't"
- "The [number] [things] you must [do/avoid] before [action]"
- "Warning: [danger] if you [common action]"
- "The hidden [thing] that's [costing/hurting] you [specific amount]"
- "A simple [technique] that [impressive result]"
- "[Counterintuitive statement]—here's why"

Mix fear-based, curiosity-based, and benefit-based.
Each fascination: 1-2 lines max.
NO FILLER. Every bullet must create urgency to learn more.""",

        "lander": f"""Write landing page copy for {niche}.

Topic/Angle: {topic}

Use conversion copywriting best practices from all the masters:

ABOVE THE FOLD:
1. HEADLINE: Big promise or pattern interrupt (Caples/Schwartz)
2. SUBHEADLINE: Expand + add specificity
3. HERO COPY: 2-3 sentences that hook them
4. PRIMARY CTA: Action-oriented button text

THE BODY:
5. PROBLEM AGITATION: Make them feel the pain (3-4 short paragraphs)
6. THE ENEMY: Who's to blame? Create an us-vs-them
7. SOLUTION INTRO: Your unique mechanism
8. BENEFIT BULLETS: 5-7 fascination-style benefits
9. SOCIAL PROOF SECTION: 3+ testimonials with specifics
10. OBJECTION HANDLING: FAQ or direct addressing
11. THE OFFER: What they get (use "stacking")
12. GUARANTEE: Bold risk reversal
13. URGENCY: Why now?
14. FINAL CTA: Repeat the action

Footer: Trust badges, fine print

Make it scan-able. Lots of white space. Bold key phrases.""",
    }
    
    prompt = script_prompts.get(script_type, f"Write compelling copy for {niche} about: {topic}")
    
    if additional_instructions:
        prompt += f"\n\nAdditional instructions: {additional_instructions}"
    
    messages = [{"role": "user", "content": prompt}]
    
    return await chat_completion(messages, context, temperature=0.8)
