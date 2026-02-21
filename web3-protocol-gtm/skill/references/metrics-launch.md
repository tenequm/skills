# Protocol Metrics and Launch Sequencing

## Metrics Deep Dive

### Instrumentation Guide

**On-Chain Metrics (Dune / Flipside / Custom)**

```
Active wallets:
  Query: Unique signers calling your program per day/week/month
  Tool: Dune Analytics dashboard with your program ID
  Frequency: Daily automated, weekly manual review

Transaction volume:
  Query: Total successful instructions to your program
  Tool: Dune or Helius webhooks for real-time
  Frequency: Real-time dashboard, weekly trend review

Protocol revenue:
  Query: Fees collected by your program (if applicable)
  Tool: Dune or custom indexer
  Frequency: Daily, reported weekly

Integration count:
  Query: Unique programs that CPI into yours
  Tool: Manual tracking + on-chain verification
  Frequency: Weekly count, monthly deep review

Attestation/record volume:
  Query: Total attestations, feedback entries, or protocol-specific data
  Tool: Your indexer or Photon RPC queries
  Frequency: Daily, reported weekly
```

**Off-Chain Metrics**

```
SDK downloads:
  Source: npm weekly downloads (npmjs.com/package/your-sdk)
  Tool: npm stats API or manual check
  Frequency: Weekly

GitHub activity:
  Source: Stars, forks, issues, PRs, contributors
  Tool: GitHub API or manual dashboard
  Frequency: Weekly

Docs engagement:
  Source: Page views, bounce rate, time on page
  Tool: Plausible, Fathom, or Cloudflare Web Analytics (privacy-respecting)
  Frequency: Weekly

Developer support:
  Source: Questions asked, response time, resolution time
  Tool: Discord/TG analytics, GitHub issue tracking
  Frequency: Weekly
```

**Community Health Metrics**

```
CT engagement:
  Source: Impressions, engagement rate, follower growth
  Tool: Twitter/X analytics
  Frequency: Weekly

Developer channel activity:
  Source: Messages, unique posters, questions answered
  Tool: Discord analytics bot or manual count
  Frequency: Weekly

Organic mentions:
  Source: Unprompted mentions of your protocol on CT/GitHub/forums
  Tool: Twitter search alerts, GitHub code search
  Frequency: Weekly
```

### Free Tooling Stack

```
On-chain:     Dune Analytics (free tier), Flipside (free tier)
Off-chain:    npm stats (free), GitHub API (free)
Docs:         Plausible ($9/mo) or Cloudflare Analytics (free)
Community:    Manual tracking in spreadsheet (free)
Dashboard:    Notion or Google Sheets (free) for internal
              Simple web page for public dashboard
```

---

## Public Metrics Dashboard

### Why Public Metrics Build Credibility

```
Public metrics signal:
  - Transparency (nothing to hide)
  - Confidence (you believe the numbers will grow)
  - Accountability (community holds you to targets)
  - Partnership value (integrators can evaluate your traction)

Keep private:
  - Revenue per integration (competitive info)
  - Specific partner pipeline (respect NDAs)
  - Team compensation/burn rate
  - Security-sensitive infrastructure details
```

### Dashboard Structure

```
Section 1: Protocol Activity (hero metrics)
  - Total integrations: [number] (all-time, with trend)
  - Active wallets (30-day): [number]
  - Transaction volume (30-day): [number]
  - Protocol records stored: [number]

Section 2: Developer Ecosystem
  - npm weekly downloads: [number] (with sparkline)
  - GitHub stars: [number]
  - Active contributors (30-day): [number]
  - Open issues / avg resolution time: [numbers]

Section 3: Community
  - CT followers: [number] (with engagement rate)
  - Developer channel members: [number]
  - Weekly questions answered: [number]

Section 4: Timeline
  - Key milestones with dates
  - Integrations shipped (chronological list)
  - Version history
```

### Implementation Options

```
Simple (1 hour):
  Google Sheet with weekly manual updates, shared publicly

Medium (1 day):
  Notion page with embedded Dune charts and manual metrics

Production (1 week):
  Custom web page pulling from Dune API + npm stats + GitHub API
  Auto-refreshing, always current
```

---

## Launch Sequencing (Full Version)

### Phase 1: Devnet/Testnet (Month 1-3)

```
Objectives:
  - Validate core functionality
  - Find and fix bugs before real money is at stake
  - Onboard first alpha testers

Week 1-4: Internal Testing
  - [ ] Deploy to devnet
  - [ ] Write comprehensive test suite (unit + integration)
  - [ ] Internal team uses protocol daily
  - [ ] Document all edge cases found

Week 5-8: Alpha Testing
  - [ ] Invite 3-5 alpha testers (hand-picked builders you trust)
  - [ ] Provide direct support (DM-level, not public channels)
  - [ ] Collect feedback weekly
  - [ ] Fix critical issues within 24 hours

Week 9-12: Security + Polish
  - [ ] Security review (self-audit at minimum, professional audit if budget allows)
  - [ ] Bug bounty program ($500-$5K range, proportional to TVL risk)
  - [ ] SDK API stabilized (no breaking changes planned)
  - [ ] Documentation complete for quickstart + main workflows

Launch Checklist:
  - [ ] All tests passing on latest commit
  - [ ] No critical or high-severity bugs open
  - [ ] 3+ alpha testers confirm "ready for wider use"
  - [ ] SDK version at 0.x.0 (not 0.0.x)
```

### Phase 2: Mainnet Beta (Month 4-6)

```
Objectives:
  - Deploy to mainnet with real usage
  - Ship first partner integrations
  - Begin public-facing growth

Week 1-2: Mainnet Deployment
  - [ ] Deploy audited code to mainnet
  - [ ] Verify on-chain (Solana Verify or equivalent)
  - [ ] Internal testing on mainnet
  - [ ] Gradual rollout (invite-only initially)

Week 3-4: First Integrations
  - [ ] Partner A integration live on mainnet
  - [ ] Partner B integration in development
  - [ ] Public docs and SDK published
  - [ ] Grant milestone 1 report submitted

Week 5-8: Public Launch
  - [ ] CT announcement thread (metrics-driven, not hype)
  - [ ] Remove invite-only restriction
  - [ ] Developer support channels open
  - [ ] First hackathon participation

Communications Plan:
  DO: Share metrics, architecture decisions, builder testimonials
  DO NOT: Overpromise, compare to competitors aggressively, hype
  Tone: "We shipped X. Here's what we learned. Here's what's next."
```

### Phase 3: Mainnet GA (Month 6-9)

```
Objectives:
  - 5+ integrations live
  - Self-sustaining developer community
  - Protocol recognized in ecosystem

Milestones:
  - [ ] 5+ integrations live and active
  - [ ] Public metrics dashboard live
  - [ ] Standards body submission (if applicable)
  - [ ] Partnership co-announcements (at least 2)
  - [ ] Developer workshop or conference presentation
  - [ ] Community can answer basic support questions without team

Growth Signals (you have traction when):
  - [ ] Teams integrate without your outreach (organic adoption)
  - [ ] CT mentions you in "best X on Solana" threads unprompted
  - [ ] Grant applications reference your protocol as infrastructure
  - [ ] Developer job postings mention experience with your protocol
```

### Phase 4: Token (Month 12+, Optional)

```
Prerequisites (ALL must be true):
  - [ ] Protocol has proven utility (real usage, not speculative)
  - [ ] Token serves a protocol function (governance, staking, fee payment)
  - [ ] Anti-sybil measures tested and deployed
  - [ ] Legal review completed (jurisdiction-specific)
  - [ ] Community governance foundation established
  - [ ] Sustainable protocol revenue (or clear path)
  - [ ] Team tokens have reasonable vesting (12+ months cliff)

Token Launch Anti-Patterns:
  - Launching token to generate interest (backwards - interest should exist)
  - Launching token before PMF (attracts speculators, not builders)
  - Airdrop without anti-sybil (farmed by bots, creates sell pressure)
  - Token as only business model (unsustainable)
  - No utility beyond speculation (regulatory risk)

If your protocol works without a token, seriously consider not launching one.
```

---

## Grant Application Anatomy

### What Grant Reviewers Look For

```
Solana Foundation:
  - Clear ecosystem benefit (not just "good for our team")
  - Working code (testnet at minimum)
  - Milestone-based plan with measurable outcomes
  - Team with relevant experience (GitHub profiles, past work)
  - Budget that is justified line-by-line
  - Applications now require Y-Combinator-level detail

Superteam:
  - Faster process, smaller grants ($5-50K typical)
  - Strong ecosystem fit with current Solana priorities
  - Active in Superteam community before applying
  - Clear deliverables within 1-3 months

Colosseum:
  - Hackathon performance is primary entry point
  - Accelerator: $250K pre-seed for top hackathon teams
  - Investment themes: DePIN, AI agents, consumer, stablecoins, infrastructure
  - Prefer teams that can ship fast (weeks, not months)
```

### Grant Application Template

```
Title: [Protocol Name] - [One-Line Description]

Problem (1 paragraph):
  [What is broken today? Who is affected? Why does this matter
  for the Solana ecosystem?]

Solution (1 paragraph):
  [What does your protocol do? How does it work at a high level?
  What makes your approach better than alternatives?]

Traction (bullet points):
  - Deployed to: [devnet/mainnet]
  - SDK version: [X.Y.Z]
  - Integrations: [number live, number in progress]
  - Developers: [number using SDK]
  - Key metric: [your north star metric and current value]

Milestones:

  M1: [Title] (Month 1)
    Deliverables: [specific, verifiable outputs]
    Success criteria: [measurable outcome]
    Budget: $[amount]
    Breakdown: [what the money pays for]

  M2: [Title] (Month 2-3)
    Deliverables: [specific, verifiable outputs]
    Success criteria: [measurable outcome]
    Budget: $[amount]
    Breakdown: [what the money pays for]

  M3: [Title] (Month 4-6)
    Deliverables: [specific, verifiable outputs]
    Success criteria: [measurable outcome]
    Budget: $[amount]
    Breakdown: [what the money pays for]

Team:
  [Name] - [Role] - [GitHub/LinkedIn] - [Relevant experience]
  [Name] - [Role] - [GitHub/LinkedIn] - [Relevant experience]

Total Budget: $[amount]

Ecosystem Benefit:
  [Why this matters beyond your protocol. What does the Solana
  ecosystem gain? Which other projects benefit?]

Open Source: [Yes/No, License type]
```

---

## Milestone Planning

### The Integration Count as North Star

For infrastructure protocols, the single most important growth metric is **number of live integrations**. Everything else follows from this:

```
More integrations = more users (via partner UIs)
More users = more on-chain activity
More activity = more revenue (if fee-based)
More revenue = sustainability
More sustainability = more integrations (confidence to depend on you)
```

### Milestone Targets by Stage

```
Month 3:   1-2 integrations (alpha partners, likely hand-held)
Month 6:   3-5 integrations (some organic, some outreach-driven)
Month 9:   8-12 integrations (ecosystem recognizes you)
Month 12:  15-25 integrations (becoming default infrastructure)
Month 18:  30-50 integrations (category leader position)
```

These are aggressive but achievable for protocols with good product-market fit and strong DevRel execution. If you are significantly below these targets, re-evaluate your ICP, your SDK quality, or your integration surface area.

### Revenue Milestones (Protocol Sustainability)

```
Stage 1: Zero revenue, funded by grants/treasury
  Duration: 6-12 months
  Focus: Adoption, integrations, developer experience

Stage 2: Non-zero revenue, not yet sustainable
  Duration: 6-12 months
  Focus: Grow usage, optimize fee structure
  Target: Protocol revenue covers hosting/infrastructure costs

Stage 3: Sustainable protocol revenue
  Duration: Ongoing
  Focus: Revenue covers core team, continued growth
  Target: Revenue grows proportionally with usage
```
