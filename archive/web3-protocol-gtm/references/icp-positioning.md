# Web3 ICP and Protocol Positioning

## Web3 ICP Framework (Full Version)

### The Three Questions

Every web3 protocol ICP starts with three questions:

1. **What are they building?** - The builder's product category
2. **What primitives do they need?** - The infrastructure gap your protocol fills
3. **Where do they live?** - The channels where you can reach them

These replace SaaS firmographics (employee count, revenue bands, industry verticals) because web3 builders do not buy through procurement - they choose tools by trying them.

### Common Builder Personas

**DeFi Builders**
```
Building: DEXs, lending protocols, yield aggregators, derivatives
Needs: Oracles, liquidity, identity, compliance, cross-chain messaging
Current solution: Chainlink, custom solutions, or nothing
Where they are: CT (DeFi accounts), DeFi-specific Discords, Ethereum/Solana dev channels
Decision process: Core dev evaluates, team discusses, ships if integration is clean
Integration bar: Must not add latency or complexity to critical paths
```

**AI Agent Builders**
```
Building: Agent marketplaces, autonomous trading bots, AI assistants, agent frameworks
Needs: Agent identity, reputation, payments (x402), tool access, memory
Current solution: Custom databases, self-issued keys, no verifiable trust
Where they are: CT (AI x crypto accounts), ElizaOS/Virtuals communities, Solana AI hackathons
Decision process: Solo dev or small team, decides fast, ships fast
Integration bar: Must work with one npm install and minimal config
```

**Payment Infrastructure Builders**
```
Building: Payment gateways, stablecoin rails, merchant tools, payroll
Needs: Identity verification, compliance, settlement, reputation
Current solution: Stripe (fiat), manual KYC, centralized trust
Where they are: x402 community, stablecoin ecosystems, fintech-crypto crossover events
Decision process: CTO or lead dev evaluates, compliance team reviews
Integration bar: Must handle edge cases gracefully, clear error messages
```

**Data and Indexing Builders**
```
Building: Block explorers, analytics platforms, indexers, data APIs
Needs: Structured on-chain data, compression-aware parsing, attestation data
Current solution: Custom indexers, Helius/Triton, The Graph
Where they are: Infrastructure-focused CT, Solana infra channels, data eng communities
Decision process: Technical lead evaluates data quality and reliability
Integration bar: Must expose clean APIs, handle chain reorgs, document edge cases
```

**Consumer App Builders**
```
Building: Wallets, social apps, gaming, NFT platforms
Needs: Identity, reputation, social graph, payments, storage
Current solution: Web2 auth (OAuth), centralized profiles
Where they are: Consumer crypto CT, gaming communities, NFT spaces
Decision process: Product lead + dev team, biased toward UX simplicity
Integration bar: Must not degrade user experience or add wallet prompts
```

### ICP Validation

Your ICP is validated when:
```
- [ ] 3+ teams matching this profile have integrated your protocol
- [ ] Integration time is under 1 day for a competent developer
- [ ] Teams that integrate retain (keep using after 30 days)
- [ ] At least 1 team found you without your outreach (organic signal)
- [ ] You can name 10+ more teams matching this profile
```

---

## Positioning Framework (April Dunford for Protocols)

April Dunford's positioning methodology works for web3 - but the components need different inputs.

### Step 1: List Competitive Alternatives

Not just direct competitors. What do builders use if your protocol does not exist?

```
Alternative types:
1. Direct competitor protocol (same primitive, same chain)
2. Cross-chain equivalent (same primitive, different chain)
3. Centralized solution (SaaS/API that solves the same problem)
4. DIY / custom code (builder rolls their own)
5. Do nothing (live without the primitive)
```

**Example (on-chain identity protocol):**
```
1. Direct: No production competitor on Solana for this primitive
2. Cross-chain: Equivalent implementations on EVM (none production yet)
3. Centralized: Custom API key systems, centralized registries
4. DIY: Teams build custom databases per platform
5. Do nothing: Users operate without verifiable identity or trust
```

### Step 2: Isolate Unique Attributes

What does your protocol have that alternatives do not?

```
Attribute types:
- Technical: Performance, cost, architecture, composability
- Ecosystem: Chain-native integration, wallet visibility, tooling support
- Standard: Backed by recognized standard (ERC/EIP/SIP)
- Economic: Gas costs, storage costs, operational overhead
```

### Step 3: Map Attributes to Builder Value

For each unique attribute, answer: "So what? Why does a builder care?"

```
Attribute: Sub-cent storage ($0.002/attestation via ZK compression)
Builder value: Can store millions of feedback records without cost concerns

Attribute: Token-2022 NFT identity (visible in Phantom/Solflare/Backpack)
Builder value: Agents show up in standard wallets without custom UI work

Attribute: Blind feedback model (cryptographic commit before outcome)
Builder value: Reputation data is trustworthy because gaming is prevented
```

### Step 4: Define Target Builders

Who cares most about these specific attributes? (This is your ICP.)

### Step 5: Choose Market Category

Three options:
```
Head-to-head:  "We are the better X" (risky - invites direct comparison)
Niche:         "We are X for [specific use case]" (safer, focused)
New category:  "We invented [new thing]" (hardest, but biggest upside)
```

Most infrastructure protocols should start with niche positioning and expand.

### Positioning Statement Template

```
For [target builders]
who need [primitive/capability],
[Protocol] is the [category]
that [key differentiation].

Unlike [primary alternative],
[Protocol] [unique advantage].
```

**Example (on-chain identity protocol):**
```
For AI agent marketplace builders
who need verifiable agent identity and reputation,
[Protocol] is the on-chain trust infrastructure
that provides cryptographically enforced feedback on Solana.

Unlike custom reputation databases,
[Protocol] stores attestations at sub-cent cost with portable,
cross-platform reputation via an open standard.
```

---

## Competitive Landscape Mapping

Web3 competitive maps are not Gartner quadrants. Use these axes:

### Mapping Axes

```
Axis 1: Decentralization spectrum
  Fully centralized <---------> Fully on-chain

Axis 2: Scope spectrum
  Single-chain native <---------> Chain-agnostic

Axis 3: Adoption spectrum
  Specification only <---------> Production with usage

Axis 4: Approach spectrum
  General-purpose <---------> Domain-specific
```

### Competitive Map Template

```
                    On-chain
                       |
            [You]      |     [Competitor A]
                       |
General ------|--------|---------|------ Domain-specific
                       |
         [Alt C]       |     [Alt B]
                       |
                   Centralized
```

Place every alternative (including "do nothing") on the map. Your positioning should own a quadrant.

---

## Narrative Construction

### The "X for Y" Formula

Works when: clear category reference, clear differentiator.

```
[Protocol] is [established concept] for [web3 context]

Good examples:
- "The identity layer for AI agents" (clear, owns a category)
- "Stripe for on-chain payments" (familiar reference, clear scope)
- "The reputation primitive for agent economies"

Bad examples:
- "The everything platform for web3" (too broad)
- "A better blockchain" (too vague, invites L1 comparison)
- "Web3 infrastructure" (means nothing specific)
```

### Narrative Building Blocks

```
1. The problem: What is broken today? (be specific, use examples)
2. Why now: What changed that makes this solvable? (timing justification)
3. The approach: How does your protocol solve it? (architecture, not features)
4. The proof: Who is already using it? (integrations, metrics, testimonials)
5. The vision: What does the world look like when this works at scale?
```

### Testing Your Positioning

Your positioning works when:
```
- [ ] A developer reads your README and knows what you do in 10 seconds
- [ ] Your CT bio makes someone click through to docs
- [ ] Integrators describe your protocol the way YOU would describe it
- [ ] You do not need to explain what category you are in
- [ ] Competitors acknowledge you exist (they position against you)
```
