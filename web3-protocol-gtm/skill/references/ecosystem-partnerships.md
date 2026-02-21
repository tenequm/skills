# Ecosystem Partnerships and Standards Adoption

## Partnership Evaluation Matrix

### Scoring Framework

Score potential partners on 4 dimensions (1-5 scale):

```
1. Technical Complementarity (weight: 35%)
   Does their protocol need your primitive?
   5 = Direct need, your protocol fills a gap in their stack
   3 = Tangential, nice to have but not critical
   1 = No real technical connection

2. Audience Overlap (weight: 25%)
   Do they reach your target builders?
   5 = Their users are exactly your ICP
   3 = Some overlap, different primary audience
   1 = No overlap

3. Team Responsiveness (weight: 25%)
   Will they actually ship the integration?
   5 = Active team, fast replies, ships regularly
   3 = Responsive but slow to ship
   1 = Unresponsive or dormant project

4. Ecosystem Credibility (weight: 15%)
   Does association with them help your reputation?
   5 = Top-tier protocol, recognized in ecosystem
   3 = Solid project, known in niche
   1 = Unknown or controversial project
```

### Partnership Priority Template

```
Partner:        [Protocol Name]
Score:          [Weighted total /5]
Integration:    [What the integration looks like technically]
Timeline:       [Estimated time to ship]
Mutual benefit: [What they get / what you get]
First step:     [Specific action to take this week]
Status:         [Not started / In discussion / Building / Live]
```

---

## Outreach Sequences

### Cold Outreach (No Existing Relationship)

```
Message 1: DM or Email (Day 1)
Subject: [Your Protocol] + [Their Protocol] integration

[Name],

I'm [your name], building [protocol] - [one-line description].

Saw that [their product] does [specific thing].
Right now [specific gap your protocol fills for them].

Integration is [X lines / one SDK call].
I built a working demo: [link or screenshot].

Worth 15 min to show you?

[Your name]


Message 2: Follow-up (Day 5, if no response)
Subject: Re: integration demo

[Name], following up - here's the working demo.

[Link to 30-second screen recording or live link]

If this is not the right time, no worries.

[Your name]


Message 3: Final (Day 12, if no response)
Subject: Last note

[Name], third and last message.

If [their product] ever needs [your primitive],
the demo is here: [link]

Will stop following up. Good luck with [their product].

[Your name]
```

### Warm Outreach (Shared Connection)

```
Through mutual connection:
"Hey [mutual], could you intro me to [name] at [protocol]?
I built a [one-line description] that could help [their product].
Have a working demo ready."

After intro:
"Thanks [mutual]. [Name], here's what I mentioned -
[link to demo or 3-sentence description].
Happy to jump on a call or just share the code."
```

### Ecosystem Fund Intro

```
When applying to ecosystem grants, mention potential partners:

"As part of this grant, we plan to integrate with
[Partner A], [Partner B], and [Partner C].
We have confirmed interest from [Partner A]
and are in discussions with [Partner B].
Grant milestone 2 includes shipped integrations."
```

---

## Integration Partnership Playbook

### From First Contact to Shipped Integration

```
Week 1: Discovery
  - Identify mutual benefit (what do they get, what do you get)
  - Technical assessment: is the integration feasible?
  - Agree on scope: what does "integrated" mean specifically?

Week 2: Build Demo
  - You build the integration on their testnet/devnet
  - Share working demo with their technical team
  - Gather feedback, adjust approach

Week 3-4: Co-develop
  - Their team reviews and integrates into their codebase
  - Joint testing on devnet
  - Documentation for their developers

Week 5: Ship
  - Deploy to mainnet
  - Joint announcement (coordinate CT posts, timing)
  - Both teams share metrics after 30 days

Week 6+: Maintain
  - Monitor integration health
  - Support their team with SDK updates
  - Explore deeper integration opportunities
```

### Integration Announcement Template

```
Joint CT Thread:

Tweet 1 (Your account):
"[Their Protocol] now uses [Your Protocol] for [capability].
Here's what this means for [user type]."

Tweet 2:
What the integration enables (specific use case)

Tweet 3:
How it works (1-2 sentence technical summary)

Tweet 4:
Metric or proof point (if available)

Tweet 5:
"Built in [X weeks]. Thanks to @their_account for the partnership.
Try it: [link]"

---

Tweet 1 (Their account):
"We integrated [Your Protocol] for [capability].
Here's why we chose them over [alternatives]."

[Continue with their perspective]
```

---

## Standards Adoption Strategy

### How Standards Get Adopted - Historical Patterns

```
ERC-20 (Token Standard):
  Adoption driver: Wallets (MetaMask) and DEXs (Uniswap) supported it
  Pattern: Reference implementation + ecosystem tooling support
  Lesson: Standards win when infrastructure supports them by default

ERC-721 (NFT Standard):
  Adoption driver: OpenSea and other marketplaces standardized on it
  Pattern: Marketplace adoption created network effects
  Lesson: Get the platforms where users interact to adopt your standard

ERC-4337 (Account Abstraction):
  Adoption driver: Wallet teams needed it for UX improvements
  Pattern: Solved a real pain (gas abstraction, social recovery)
  Lesson: Standards that solve felt pain get adopted faster

Common pattern:
  Real problem -> Spec + reference impl -> 3-5 early adopters ->
  tooling support -> network effects -> de facto standard
```

### Standards Adoption Playbook

```
Phase 1: Ship Code, Not Specs (Month 1-3)
  - Reference implementation deployed and working
  - At least 1 project using it in production (ideally yours)
  - Spec document exists but code is the primary artifact
  - "Here's a working implementation" beats "here's a specification"

Phase 2: Recruit Early Adopters (Month 3-6)
  - Identify 3-5 high-profile projects that would benefit
  - Help them integrate (do the work, not just provide docs)
  - Each adopter validates the standard and surfaces edge cases
  - Iterate on the spec based on real implementation feedback

Phase 3: Build Tooling (Month 6-9)
  - SDK that makes implementing the standard trivial
  - Explorers/dashboards that understand the standard
  - Verification tools (is this implementation compliant?)
  - Documentation for implementers (not just users)

Phase 4: Formalize and Advocate (Month 9-12)
  - Submit to relevant standards body (EIP for Ethereum, SIP for Solana)
  - Present at ecosystem conferences and developer events
  - Write educational content on why the standard exists
  - Show up consistently to working groups and governance discussions

Phase 5: Ecosystem Effects (Month 12+)
  - Wallets, explorers, and tooling support the standard natively
  - New projects adopt it by default
  - Network effects make it costly NOT to use the standard
```

### Standards Adoption Checklist

```
- [ ] Reference implementation is MIT licensed
- [ ] Implementation is forkable in under 1 hour
- [ ] Spec document explains the "why" (not just the "what")
- [ ] 3+ independent implementations exist
- [ ] Tooling exists for verification/compliance
- [ ] Active maintainer responds to issues and PRs
- [ ] Backward compatibility strategy documented
- [ ] Migration path from alternatives documented
```

---

## Composability as GTM

### Designing for Maximum Composability

```
Your protocol's composability surface determines its growth ceiling.

High composability:
  - Clean, typed SDK with well-documented functions
  - CPI-friendly on-chain program (other programs can call yours)
  - Predictable costs and latency
  - Idempotent operations where possible
  - Events/logs that other protocols can index

Low composability:
  - Requires custom infrastructure to integrate
  - Non-standard data formats
  - Unpredictable costs or latency spikes
  - Stateful operations that create race conditions
  - No events/logs for other protocols to consume
```

### The Composability Flywheel

```
Make integration easy
       |
       v
More protocols integrate
       |
       v
More users interact with your protocol (through partner UIs)
       |
       v
More data/activity on your protocol
       |
       v
Your protocol becomes more valuable (network effects)
       |
       v
More protocols want to integrate (FOMO + real value)
       |
       v
[Cycle repeats]
```

### Composability Audit

```
Ask these questions about your protocol:

- [ ] Can another program CPI into yours without custom setup?
- [ ] Can a developer integrate in under 1 day?
- [ ] Can integration work without contacting your team?
- [ ] Are there working examples of integration patterns?
- [ ] Does your SDK handle all the complexity internally?
- [ ] Can partners index your on-chain events easily?
- [ ] Is your protocol usable as a dependency, not just standalone?

Every "no" is a growth ceiling.
```

---

## Grant Partnerships

### Joint Grant Applications

When two protocols apply together, success rates improve because:
- Demonstrates ecosystem thinking (funders love this)
- Shows concrete integration plan (not vague "we will partner")
- Shared milestones create mutual accountability

### Joint Grant Template

```
Title: [Protocol A] + [Protocol B] Integration for [Ecosystem Benefit]

Problem:
  [Builders need X, but today A and B are disconnected.
  This forces builders to Y, which causes Z.]

Solution:
  [Integrate A's primitive into B's workflow so builders get
  X without manual effort.]

Milestones:
  M1 (Month 1): Technical spec + devnet prototype
    Deliverable: Working demo on devnet
    Success criteria: [specific test passing]
    Budget: $X (split: A gets $Y, B gets $Z)

  M2 (Month 2): Integration shipped to mainnet
    Deliverable: Production integration live
    Success criteria: [first 3 users/transactions]
    Budget: $X

  M3 (Month 3): Adoption + documentation
    Deliverable: SDK support, docs, case study
    Success criteria: [5+ builders using integration]
    Budget: $X

Team:
  Protocol A: [names, GitHub profiles, relevant experience]
  Protocol B: [names, GitHub profiles, relevant experience]

Total Budget: $X
Ecosystem Benefit: [Why this matters beyond just A and B]
```
