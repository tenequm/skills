# Developer Relations for Web3 Protocols

## The DevRel Bottleneck

Traditional DevRel is your biggest bottleneck (DoraHacks, Feb 2026). The math is brutal: 5 DevRel people serving 5,000 active developers = 1,000 devs per person = 5 minutes of attention per month per developer. Three fatal flaws:

1. **Capacity ceiling** - DevRel team hours are the hard limit on ecosystem growth
2. **Information black hole** - teams cannot see who's building, where they're stuck, or when they're about to leave
3. **Reactive, not proactive** - firefighting kills proactive outreach

The solution is the DevRel Stack (Levels 1-5 below) combined with Agentic DevRel (Level 6) to break through the capacity ceiling.

## The DevRel Stack

### Level 1: Documentation (Foundation)

Documentation is the single highest-leverage investment for protocol growth. In 2026, developers query Claude, GPT, and Copilot before reading docs. If your docs are not AI-parseable, your protocol is invisible.

**AI-Readable Documentation Checklist:**
```
Structure:
- [ ] Consistent heading hierarchy (H1 > H2 > H3, no skipped levels)
- [ ] Every code block has a language tag (```typescript, ```bash)
- [ ] No critical information embedded in images
- [ ] Parameters documented with types, defaults, and constraints
- [ ] Return values documented with types and examples
- [ ] Error codes listed with causes and fixes

Content:
- [ ] 5-minute quickstart that works (copy-paste, run, see result)
- [ ] Every example uses real values (not YOUR_API_KEY or <placeholder>)
- [ ] Happy path AND error path documented
- [ ] Prerequisites listed explicitly (node version, dependencies)
- [ ] Changelog maintained with dates and migration guides

Discovery:
- [ ] llms.txt file at docs root (or equivalent structured index)
- [ ] Sitemap for search engines
- [ ] OpenAPI/Swagger spec for API endpoints
- [ ] README links directly to quickstart
```

**Documentation Quality Test:**
```
1. Give your quickstart to a developer who has never seen your protocol
2. Time them: can they get a working result in under 5 minutes?
3. If not: the docs are the problem, not the developer
4. Repeat until 5-minute target is consistently hit
```

### Level 2: SDK Design

**Principles:**
```
1. One install command: npm install @your-org/sdk
2. Typed from the start (TypeScript with full type exports)
3. Sensible defaults (works with zero config for devnet)
4. Progressive complexity (simple things are simple, complex things are possible)
5. Errors are clear (not "Transaction failed" - say WHY)
```

**SDK Quality Checklist:**
```
- [ ] Works with one npm install (no peer dependency hell)
- [ ] TypeScript types included (not @types/ separate package)
- [ ] Quickstart example runs in under 10 lines of code
- [ ] Default network is devnet (safe for experimentation)
- [ ] Mainnet requires explicit opt-in
- [ ] All async operations return typed results
- [ ] Error messages include what went wrong AND what to do
- [ ] Bundle size is reasonable (< 500KB for browser)
- [ ] Tree-shakeable (unused functions do not bloat bundles)
- [ ] Tests pass on every commit (CI/CD)
```

**Anti-patterns:**
```
Bad: require 20 lines of config before first SDK call
Bad: force users to manage connection/client lifecycle
Bad: untyped responses that require manual parsing
Bad: different APIs for devnet vs mainnet
Bad: error messages that only show error codes
```

### Level 3: Examples

Working reference implementations that developers can fork and modify.

```
Minimum example set:
1. Quickstart (10 lines, simplest possible usage)
2. Full workflow (end-to-end, covers primary use case)
3. Integration example (how to add your protocol to an existing app)
4. Advanced example (custom configuration, edge cases)

Each example must:
- [ ] Run without modification (no placeholders to fill in)
- [ ] Include a README with what it demonstrates
- [ ] Be tested in CI (examples that break are worse than no examples)
- [ ] Use the same SDK version as docs reference
```

### Level 4: Developer Support

```
Response time targets:
  GitHub issues:    < 24 hours for first response
  Discord/TG dev:   < 30 minutes during business hours
  CT DMs:           < 4 hours

Support quality standards:
- Answer the actual question (not "read the docs")
- Include code snippets in answers
- If it is a bug, acknowledge and create a tracking issue
- If it reveals a docs gap, fix the docs immediately
- Tag resolved issues for future searchability
```

### Level 5: Developer Content

```
Content types (ranked by developer value):
1. Architecture decisions ("Why we chose X over Y")
2. Integration tutorials ("How to add [protocol] to your [framework]")
3. Performance benchmarks ("Attestation costs: before and after compression")
4. Migration guides ("Upgrading from v0.10 to v0.11")
5. Ecosystem overviews ("The agent identity landscape on Solana")
```

### Level 6: Agentic DevRel

One DevRel person augmented by AI agents can now do what used to require a team of twenty. This is the breakthrough that makes DevRel scale.

**What agents handle:**
```
Proactive tracking:
  - Monitor GitHub commits across your ecosystem
  - Detect when active builders go inactive (churn risk)
  - Follow up automatically with context-aware messages
  - Surface new repos integrating your SDK

Smart triage:
  - Flag high-potential builders for human follow-up
  - Score builders by activity, quality, and ecosystem fit
  - Route support questions to the right human expert
  - Identify patterns in developer friction (repeated questions = docs gap)

Instant support:
  - 24/7 answers in all languages
  - Trained on your docs, SDK, and past support conversations
  - Escalate edge cases to humans with full context
  - Auto-update when docs change

Data-driven insights:
  - Which builders are stuck and on what
  - Which builders are about to churn
  - Which integrations are growing vs stalling
  - Developer funnel metrics updated in real-time

Personalized outreach:
  - Context-aware messages based on what each builder is actually building
  - Milestone congratulations (first mainnet deploy, first 100 users)
  - Relevant hackathon/grant recommendations
```

**The acquisition + retention split:**
```
Hackathons = acquisition engine (get developers in the door)
Agentic DevRel = retention engine (keep them building, catch them before they leave)
```

**Developer retention benchmarks:**
```
Enable "tangible success within 5 minutes" during onboarding
Multi-layered incentive stack: on-chain recognition, progressive ownership
Avoid "ghost developer activity" - attract authentic builders with mission-driven narratives
Full-time crypto developers rose 5% YoY in 2025 (Electric Capital)
```

---

## Hackathon Playbook

### The Hackathon Landscape (2026)

Hackathons have matured from grassroots weekend events into a structured talent pipeline with measurable ROI. Key stats:

- Colosseum Solana hackathons: 80,000+ total participants, 150+ countries, 50+ venture-backed startups, $700M+ cumulative alumni funding
- ETHGlobal: 68+ events total, $2.7M+ in annual prize distribution, record $800K single-event pool (Bangkok 2024)
- DoraHacks: Multi-chain ecosystem hackathons and quadratic grant rounds, 11,774 hackers in single event

**Notable hackathon-to-unicorn stories:**
- 1inch: ETHGlobal NYC 2019 -> unicorn Dec 2020 (18 months) -> ~$500B total swap volume
- CryptoKitties/Dapper Labs: ETHWaterloo 2017 -> $7.6B valuation -> spawned ERC-721 standard
- Jito, Tensor, Drift, Marinade, Squads, STEPN: All Solana hackathon graduates

**Tier 1 hackathons (2026):**
```
Colosseum (Solana):  2 major hackathons/year + Eternal perpetual program
                     Hackathon -> Eternal -> Accelerator ($250K pre-seed)
                     0.67% accelerator acceptance rate

ETHGlobal:           6+ in-person events/year across 5 continents
                     Plus virtual ETHOnline annually
                     Created invite-only Trifecta for past finalists

DoraHacks:           Multi-chain ecosystem hackathons
                     Quadratic grant rounds integrated

Alliance DAO:        MVP Tournaments -> Accelerator ($500K funding)
                     $3.5M median post-program raise
```

### Sponsor Bounty Structure That Works

```
Three-tier bounty model:

Tier 1: Pool Prizes ($100-500 per qualifying project)
  Purpose: Maximum adoption and integration breadth
  Example: Blockscout at ETHGlobal Prague - pool prizes got 37% of all
  projects (81 out of 217) to integrate. 7 of 10 overall finalists used them.
  This is the highest-ROI tier for protocol adoption.

Tier 2: Track Prizes ($5K-15K for top 3 in your category)
  Purpose: Quality incentive for deeper integrations
  Structure: 1st ($X), 2nd ($Y), 3rd ($Z) + honorable mentions

Tier 3: Follow-on Grants ($30K+ for winning teams that keep building)
  Purpose: Convert hackathon energy into ongoing development
  Example: Movement Labs - $3,500 USDC hackathon prizes + $30K in later grants

Total budget guidance:
  Tier 2 events (chain-specific, smaller): $15K-30K total
  Tier 1 events (ETHGlobal, Colosseum):   $50K-100K total
```

**Critical rule:** Sponsors must distribute prizes if there are eligible submissions. Denying an eligible prize for quality reasons is worse for your reputation than paying it (Devpost official guidance).

### Pre-Hackathon (2 Weeks Before)

```
Bounty Design:
- [ ] Clear prize with published judging criteria (innovation, completeness, use of protocol)
- [ ] Bounty requires meaningful integration (not just "mention us")
- [ ] Prize structure follows three-tier model (pool + track + follow-on)

Preparation:
- [ ] "Hackathon quickstart" docs page (stripped down, copy-paste ready)
- [ ] Boilerplate repo teams can fork (working example with your SDK)
- [ ] Ensure SDK works with AI coding tools (Cursor, Claude Code autocomplete)
- [ ] Workshop scheduled (30-45 min, live-coding format)
- [ ] Support channel created (dedicated Telegram group or Discord channel)
- [ ] Team availability schedule posted (who is on-call, when)
- [ ] No-API-key access for limited usage (friction kills adoption at hackathons)
```

### During Hackathon

```
Support (this is the highest-ROI activity):
- [ ] Staff engineers physically present at in-person events
- [ ] Response time target: < 30 minutes for technical questions
- [ ] Office hours: 2x during hackathon (30 min each, open Q&A)
- [ ] Proactive outreach: message teams building on your protocol
- [ ] Debug sessions: offer 1:1 help to stuck teams
- [ ] "The team was always available and quickly unblocked us" = what winning
      teams say about the best sponsors

Engagement:
- [ ] CT updates: "X teams building on [protocol] at [hackathon]"
- [ ] Retweet/amplify teams that share their progress
- [ ] Internal tracking: which teams, what they are building, blockers hit
- [ ] Approach teams early - don't wait for them to come to you
```

### Post-Hackathon

```
Follow-up sequence (the window closes fast - act within 48 hours):
Day 1:  Announce winners, congratulate all participants on CT
Day 3:  DM every team that built on your protocol (winners + non-winners)
Day 7:  Offer to help winning teams ship to mainnet
Day 14: Check in on progress, remove blockers
Day 30: Feature shipped integrations on your CT and docs

Tracking:
- [ ] Teams that used your protocol: [number]
- [ ] Teams that completed working integration: [number]
- [ ] Teams continuing to build post-hackathon: [number]
- [ ] Teams that shipped to mainnet: [number] (the metric that matters)
- [ ] Teams that entered accelerators: [number]

Reality check: Only ~15% of winning projects continue development.
Your follow-up determines whether your investments are in that 15%.
```

### Hackathon ROI Measurement

```
Cost:
  Bounty prize pool:          $X
  Workshop preparation:       Y hours
  Support during hackathon:   Z hours
  Follow-on grants:           $W
  Total cost:                 $(X+W) + ((Y+Z) hours * hourly rate)

Return:
  Teams that integrated:      [number]
  Teams that shipped mainnet: [number]
  Ongoing integrators:        [number]
  Teams that raised funding:  [number]

Cost per integration = Total cost / Teams that shipped mainnet

Benchmark: < $2K per mainnet integration is excellent ROI
```

### The Hackathon-to-Fund Pipeline

The hackathon is no longer a standalone event - it's the top of a structured funnel.

```
Hackathon submission (1,500+ teams)
       |
       v
Bounty winners (top 5-10%)
       |
       v
Post-hackathon follow-up + grants ($5K-50K)
       |
       v
Accelerator application (Colosseum: 0.67% acceptance)
       |
       v
Pre-seed funding ($250K-500K)
       |
       v
Venture raise ($3.5M median post-program, Alliance data)
```

**Grants + hackathon performance:**
- Colosseum: Hackathon -> Eternal -> Accelerator is the designed funnel. Investment evaluation explicitly considers hackathon iteration
- Solana Foundation: Hackathon wins are strong social proof for grant applications (not automatic admission, but a de facto credential)
- Alliance DAO: MVP Tournaments feed directly into accelerator ($500K funding)
- General pattern: Hackathon results are the best "working demo" you can bring to any grant application

### Winning Hackathon Strategies (For Builders)

What judges evaluate across ETHGlobal, Colosseum, and DoraHacks:

```
1. Usability (UI/UX/DX) - Is the interface clear, fast, pleasant?
2. Practicality - Can someone use this today? End-to-end user journey matters
3. Originality - Novel mechanism, unique UX, clever remix of primitives?
4. Technicality - Is the problem non-trivial? Beyond a simple frontend wrapper?
```

**The P-A-C-E idea filter:**
```
Pain       - Does this solve a real developer or user pain point?
Atomicity  - Can you build and demo one complete user action in the timeframe?
Composable - Does it lean on existing primitives (oracles, AA, cross-chain)?
Ecosystem  - Is it relevant to the event's judges, sponsors, and audience?
```

**48-hour time allocation:**
```
Hours 0-6:   First full vertical slice of core loop
Hours 6-24:  Harden critical path, add minimal landing page, error handling
Hours 24-40: Record backup demo video, start writing submission text
Hours 40-48: FREEZE FEATURES. 15% of total time reserved for polish, video, README

Common mistake: Teams code until the last minute and submit a terrible video.
The video and README are often the ONLY thing judges see in the first round.
```

**Team composition (sweet spot: 2-4 people):**
```
- Smart contracts / protocol engineer
- Front-end / DX builder
- Product / story person (scope keeper, demo narrator)
- Optional: dedicated designer (a "secret weapon" for perceived quality)
```

**Pre-event preparation:**
```
- Study sponsor technologies and bounties weeks before the event
- Set up dev environment completely - don't waste hours on config
- Pre-bake scaffolds: auth flows, wallet connections, deployment scripts
- Clone boilerplate repos and have starter code ready
- Join hackathon Discord early - most teams form before the event
- Watch previous finalists' presentations to understand what judges want
```

**Bounty targeting:**
```
- Don't chase more than 2 sponsor bounties (unless technologies overlap)
- Mirror the sponsor's rubric - use their keywords, reference their APIs
- Register for each prize explicitly (some platforms require "Start Work" button)
- Approach sponsors early during the event - pitch your idea, get their input
- Watch for less crowded tracks - fewer submissions = better odds
```

### AI Tooling at Hackathons

AI coding tools (Cursor, Claude Code, Copilot) have fundamentally changed hackathon dynamics:

```
What's changed:
- Non-engineers can produce working prototypes ("vibe coding")
- Higher baseline quality expected since AI handles boilerplate
- Solo developers can ship what used to require a full team
- Judges weight originality and insight higher, implementation polish lower

What works:
- Use AI to eliminate boilerplate, not to substitute for domain expertise
- Pre-bake templates that work well with AI assistance
- Focus creative energy on the novel mechanism, let AI handle commodity code

What doesn't:
- "1-shot or bust" - AI-generated codebases that fail the first attempt
  become messy, sprawling, and impossible to debug
- Pure vibe-coded projects are brittle and impossible to maintain post-hackathon
- Judges can tell the difference between AI-generated polish and genuine insight

For sponsors:
- Ensure your SDK works with AI coding assistants (autocomplete, inline docs)
- Provide LLM-parseable documentation
- Don't penalize AI usage (it's table stakes) - do penalize lack of originality
```

### Hackathon Fatigue and Quality

```
The problem:
- ~70% of attendees at major events are returning builders
- Same teams appear across ETHGlobal, Colosseum, DoraHacks circuits
- Some teams clearly prepare weeks in advance despite "start fresh" rules
- Mid-tier hackathons face diminishing returns

How organizers respond:
- ETHGlobal: Invite-only Trifecta for past finalists, first-time hacker tracks
- Colosseum: Sub-1% accelerator acceptance naturally filters for quality
- Code provenance: Repos must show gradual commit history, not mega-commits
- Category prizes (Best Student, Best First-Time) encourage new entrants

Recommendation for protocols:
- Target tier 1 events (ETHGlobal, Colosseum) for quality over quantity
- Use pool prizes to cast a wide net, track prizes for depth
- Focus post-hackathon energy on the teams that keep building, not just winners
```

---

## Developer Funnel

### Stages and Conversion Benchmarks

```
Stage 1: Discovery
  How: CT threads, hackathons, docs search, AI tool suggestions
  Metric: Docs page views, GitHub repo visitors
  Benchmark: 1000+ monthly visitors for growing protocol

Stage 2: First Touch
  How: Developer reads quickstart, clones example repo
  Metric: Quickstart page views, repo clones, npm installs
  Benchmark: 10-15% of visitors attempt quickstart

Stage 3: Integration
  How: Developer installs SDK, makes first successful call
  Metric: npm installs with actual usage (not just install)
  Benchmark: 30-50% of quickstart attempts succeed

Stage 4: Production
  How: Developer deploys integration to mainnet
  Metric: Active wallets calling your program, mainnet transactions
  Benchmark: 20-30% of successful integrations go to production

Stage 5: Advocacy
  How: Developer writes about you, refers others, contributes back
  Metric: Organic CT mentions, GitHub PRs, referral integrations
  Benchmark: 5-10% of production users become advocates
```

### Funnel Optimization

```
If Discovery is low:
  - Increase CT posting frequency
  - Submit to more hackathons
  - Improve SEO on docs
  - Get listed in ecosystem directories

If First Touch drops off:
  - Quickstart is too complex (simplify)
  - Docs are confusing (user test with real developer)
  - Prerequisites are unclear (make explicit)

If Integration fails:
  - SDK has rough edges (improve error messages)
  - Examples are broken (test in CI)
  - Common use case is not documented

If Production conversion is low:
  - Devnet-to-mainnet migration is painful (simplify)
  - Mainnet costs are prohibitive (optimize)
  - Performance is not production-ready

If Advocacy does not happen:
  - You are not engaging with builders who ship
  - No recognition program (highlight builders on CT)
  - No way for builders to contribute back (no open issues)
```

---

## Workshop Template

### Structure (45 minutes)

```
0:00 - 0:05  Context
  What problem does your protocol solve?
  Who is using it today? (1-2 examples)
  What will attendees build in this workshop?

0:05 - 0:15  Live Demo
  Show the end result first (what they will have built)
  Walk through the code, explain key decisions
  Highlight: "this is the part that usually trips people up"

0:15 - 0:40  Hands-On Coding
  Attendees code along or fork the boilerplate repo
  You code on screen, they follow
  Pause every 5 minutes: "Where is everyone? Any errors?"
  Have a second person monitoring chat for stuck attendees

0:40 - 0:45  Q&A + Next Steps
  Common questions and answers
  Where to go next (docs, Discord, examples)
  Bounty reminder if during a hackathon
```

### Workshop Preparation Checklist

```
- [ ] Boilerplate repo ready (tested, runs without modification)
- [ ] Devnet deployed and working (verify day-of, not day-before)
- [ ] Slides: max 10, mostly code screenshots
- [ ] Backup plan: pre-recorded video if live coding fails
- [ ] Second person available for chat support
- [ ] Post-workshop resources page with all links
```
