# Developer Relations for Web3 Protocols

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

---

## Hackathon Playbook

### Pre-Hackathon (2 Weeks Before)

```
Bounty Design:
- [ ] Clear prize: "$X for best project using [your protocol]"
- [ ] Judging criteria published (innovation, completeness, use of protocol)
- [ ] Bounty requires meaningful integration (not just "mention us")
- [ ] Prize tiers: 1st ($X), 2nd ($Y), 3rd ($Z) + honorable mentions
- [ ] Budget: $2K-10K total (proportional to hackathon size)

Preparation:
- [ ] "Hackathon quickstart" docs page (stripped down, copy-paste ready)
- [ ] Boilerplate repo teams can fork (working example with your SDK)
- [ ] Workshop scheduled (30-45 min, live-coding format)
- [ ] Support channel created (dedicated Telegram group or Discord channel)
- [ ] Team availability schedule posted (who is on-call, when)
```

### During Hackathon

```
Support:
- [ ] Response time target: < 30 minutes for technical questions
- [ ] Office hours: 2x during hackathon (30 min each, open Q&A)
- [ ] Proactive outreach: message teams building on your protocol
- [ ] Debug sessions: offer 1:1 help to stuck teams

Engagement:
- [ ] CT updates: "X teams building on [protocol] at [hackathon]"
- [ ] Retweet/amplify teams that share their progress
- [ ] Internal tracking: which teams, what they are building, blockers hit
```

### Post-Hackathon

```
Follow-up sequence:
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
```

### Hackathon ROI Measurement

```
Cost:
  Bounty prize pool:          $X
  Workshop preparation:       Y hours
  Support during hackathon:   Z hours
  Total cost:                 $X + (Y+Z hours * hourly rate)

Return:
  Teams that integrated:      [number]
  Teams that shipped mainnet: [number]
  Ongoing integrators:        [number]

Cost per integration = Total cost / Teams that shipped mainnet

Benchmark: < $2K per mainnet integration is excellent ROI
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
