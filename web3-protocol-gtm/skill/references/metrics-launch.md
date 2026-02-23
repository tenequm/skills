# Protocol Metrics and Launch Sequencing

## Revenue Is the North Star

The industry has decisively shifted from TVL to revenue as the primary success metric.

**1kx 2025 Onchain Revenue Report (the definitive source):**
```
- On-chain economy: $20B in fees, $9.7B in H1 2025 alone (41% YoY growth)
- 1,124 protocols achieved profitability in 2025
- 389 protocols started generating fees for the first time in 2025
- Nearly 400 protocols with $1M+ ARR
- 71 protocols exceeded $100M in on-chain ARR
- Value distributed to token holders hit ATH for 3 consecutive quarters ($1.9B in Q3)
- Top apps cut token incentives from $2.8B (90% of fees) to <$0.1B - almost all
  value now flows to holders rather than being subsidized
```

**Artemis "Crypto Revenue" standard (Sep 2025):**
Proposed industry-standard definition for "revenue" as value accrual to token holders. Protocols operate as multi-sided marketplaces - metrics should reflect this. 10+ protocols and funds adopted the framework.

**TVL is now considered misleading:** "TVL is the biggest lie in crypto." Classic recursive loop: deposit $100 ETH, borrow $80, swap to ETH, deposit again = $180+ TVL from $100 real capital. A massive chunk of DeFi TVL is just leverage masquerading as adoption.

**What metrics matter now:**
```
1. Protocol revenue (fees accruing to token holders) - THE primary metric
2. Active addresses / daily transactions (273M monthly active wallets in H1 2025)
3. Fee-to-valuation ratio (P/F ratio) - DeFi median 17x vs Blockchain median 3,902x
4. Revenue growth rate
5. Value distributed to token holders (buybacks, burns, staking net of emissions)
6. Developer activity (full-time crypto developers rose 5% YoY, Electric Capital)
```

---

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
  - [ ] Legal review completed (jurisdiction-specific, see regulatory section)
  - [ ] Community governance foundation established
  - [ ] Sustainable protocol revenue (or clear path)
  - [ ] Team tokens have reasonable vesting (12+ months cliff)

Token Launch Anti-Patterns:
  - Launching token to generate interest (backwards - interest should exist)
  - Launching token before PMF (attracts speculators, not builders)
  - Airdrop without anti-sybil (farmed by bots, creates sell pressure)
  - Token as only business model (unsustainable)
  - No utility beyond speculation (regulatory risk)
  - Generic airdrop farming incentives (returns barely cover participant time cost)

If your protocol works without a token, seriously consider not launching one.
```

### The Hyperliquid Airdrop Model (Gold Standard)

Hyperliquid's HYPE token launch (Nov 2024) is the defining case study for how airdrops should work:

```
What they did:
  - 31% of supply airdropped (vs. typical 5-15%)
  - Zero VC backing, zero private investor allocations
  - $1.7B market cap on day one, grew to $40B valuation by mid-2025
  - $550M annualized revenue, $300B monthly trading volume
  - 60%+ market share in decentralized derivatives
  - Daily token buybacks creating deflationary pressure

Why it worked:
  - Genuine product-market fit FIRST, then airdrop (not the reverse)
  - Generous allocation to actual users, not insiders
  - Revenue-backed token (not speculative)
  - No VC dump risk at unlock

Key lesson:
  Build in relative quiet, achieve genuine PMF, then distribute generously.
  The reverse order (GTM before PMF) is increasingly failing.
```

### Airdrop Reality Check (2026)

```
What's dead:
  - "Didn't Make Money, But At Least Got Tired" (Bitget 2025 review title)
  - Number of participants rises, returns barely cover time cost
  - Rules constantly adjusted, thresholds raised, random factors increased
  - Generic airdrops with one-time snapshots attract mercenary capital

What works:
  - Milestone-based distribution tied to genuine protocol usage
  - PMF before distribution (Hyperliquid model)
  - Anti-sybil from day 1 (not bolted on after farming is discovered)
  - "Fairer launchpads replacing opportunistic airdrops with milestone-based funding"
```

### Regulatory Environment for Tokens (2026)

Compliance has become a competitive advantage. Key regulations:

```
United States:
  - SEC enforcement actions against unregistered airdrop distributions
  - IRS treats every airdropped token as taxable ordinary income
  - Wash trading coordination during airdrops can trigger CFTC enforcement
  - Clarity Act and Genius Act creating clearer but stricter frameworks
  - US users increasingly excluded from major airdrops

Europe:
  - MiCA (Markets in Crypto-Assets) regulation in effect
  - Clear licensing requirements for token issuers
  - Consumer protection requirements

General:
  - Dragonfly published 58-page academic paper on airdrop effectiveness
    and regulatory implications (2025)
  - Legal review is no longer optional - it's prerequisite
  - Jurisdiction selection matters: some jurisdictions are actively hostile,
    others provide regulatory clarity
  - "Compliance has become a competitive advantage" (ICODA, Oct 2025)
```

---

## Grant Application Anatomy

### What Grant Reviewers Look For

```
Solana Foundation ($100M+ distributed, 500+ projects):
  - Clear ecosystem benefit (not just "good for our team")
  - Working code (testnet at minimum)
  - Milestone-based plan with measurable outcomes
  - Team with relevant experience (GitHub profiles, past work)
  - Budget that is justified line-by-line
  - Applications now require Y-Combinator-level detail
  - Types: Milestone-based, convertible grants, RFPs

Superteam:
  - Faster process, smaller grants ($5-50K typical)
  - Strong ecosystem fit with current Solana priorities
  - Active in Superteam community before applying
  - Clear deliverables within 1-3 months

Colosseum:
  - Hackathon performance is primary entry point
  - Accelerator: $250K pre-seed for top hackathon teams (0.67% acceptance rate)
  - Eternal program: $25K award + $250K pre-seed for accelerator admission
  - Investment themes: DePIN, AI agents, consumer, stablecoins, infrastructure
  - Prefer teams that can ship fast (weeks, not months)

Optimism Retro Funding:
  - Shifted from annual rounds to continuous rewards (Season 7-8)
  - Algorithm-driven scoring: builders love steady payouts and data-backed evaluation
  - Focus areas: Dev Tooling, Onchain Builders
  - Monthly payouts vs. one-time grants

Arbitrum:
  - $10M Audit Program (12 months, smart contract audits)
  - ArbiFuel: Gas fee sponsorship for early-stage teams
  - Gaming Catalyst Program for gaming-specific grants
  - Domain Allocators for specialized funding areas

Alliance DAO:
  - $500K funding upon admission, $450K investment required
  - Median startup raises $3.5M after program
  - MVP Tournament: Up to $500K + accelerator spot
  - 1,700+ applications per cohort, ~20 accepted

Gitcoin Grants:
  - $60M+ distributed to date
  - Quadratic funding rounds
  - Strong for public goods and open-source tooling
```

**Hackathon results as grant credential:**
Hackathon wins are the best "working demo" you can bring to any grant application. Colosseum's pipeline explicitly evaluates hackathon iteration. Solana Foundation treats wins as strong social proof. Alliance MVP Tournaments are designed as direct grant feeders.

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
