# Token Launch Playbook

Tactical guide for launching tokens on Solana as a solo builder. Covers launchpad mechanics, timing, community tactics, and survival strategies. Updated for February 2026.

---

## When to Launch a Token (and When Not To)

### Launch a Token If:

```
- Your product has real users (even 50-100)
- The token serves a protocol function (governance, staking, fee payment, access)
- You have capacity to manage post-launch community (72+ hours of active attention)
- You understand the regulatory environment in your jurisdiction
- You have product-market fit or strong signal of it
```

### Do NOT Launch a Token If:

```
- You are trying to generate interest in a product nobody uses yet
- Token is your only business model (unsustainable)
- You are in the middle of a hackathon build sprint
- You cannot dedicate 72+ hours of focused attention post-launch
- You have not consulted jurisdiction-specific legal guidance
- Your product works fine without a token
```

The Hyperliquid model is the gold standard: build in relative quiet, achieve genuine PMF, then distribute generously. 31% of supply airdropped after $550M annualized revenue, zero VC backing. The reverse order (token before PMF) is increasingly failing.

---

## Launchpad Mechanics (Solana, February 2026)

### Pump.fun

The dominant Solana launchpad. 51.2% market share, 66% of all Solana token creations.

```
Creation:
  - Cost: ~0.015 SOL (~$2)
  - Supply: 1 billion tokens (fixed)
  - ~793.1M tokens allocated to bonding curve
  - ~206.9M tokens reserved for post-graduation PumpSwap pool
  - Curve: Constant-product (x * y = k), initialized with 30 virtual SOL
  - Fee: 1.25% per transaction (0.3% to creator, 0.95% to pump.fun)

Graduation:
  - Threshold: 115 total SOL (30 virtual + 85 real from traders)
  - Market cap at graduation: ~$69-100K (depends on SOL price)
  - Graduation rate: 0.63% overall (arXiv study, 655K tokens analyzed)
    Recent high: 1.15% (Feb 2026)
  - Median time to graduation: 4.4 minutes
  - Median trades to graduation: 457 swaps
  - Daily launches: 72,000+
  - Average non-graduated token lifespan: ~9 hours

Post-Graduation (PumpSwap):
  - Migration: Instant and free (replaced Raydium March 2025)
  - LP tokens: Burned at graduation (no rug on initial liquidity)
  - Swap fee: 0.25% (0.20% to LPs, 0.05% to protocol)
  - Graduation fee: 1.5 SOL
  - Initial liquidity: ~$10-15K (thin)

What predicts graduation (academic finding):
  - Fast liquidity accumulation through FEW large trades (not many small ones)
  - "Liquidity velocity" is the single strongest predictor
  - High bot activity (>70%) = LOWER graduation probability
  - Non-bot (retail) participation correlates with higher graduation
  - 92.2% of tokens with 30+ swaps exhibit dump events
```

### Bags.fm

Fastest-growing alternative, 33.5% market share. Briefly surpassed Pump.fun in January 2026.

```
  - Launch cost: 0.05 SOL (~$3)
  - Bonding curve: Meteora DBC (different from Pump.fun)
  - Creator revenue: 1% of ALL trading volume forever
  - Social account verification built in
  - $1B+ total volume in under 30 days
  - Best for: Creators who can drive sustained trading volume
  - If token does $10M volume, creator earns $100K
```

### Believe App

SocialFi launchpad. Launch by replying to @launchcoin on X with a ticker.

```
  - No wallet or coding required to initiate
  - Fee: 2% transaction (1% creator, 1% platform)
  - Launches typically at 20:00 ET (except Fridays)
  - $200M trading volume within days of May 2025 launch
  - Best for: Founders with existing X/Twitter following
```

### Moonshot

Higher quality signal due to higher graduation threshold.

```
  - Launch cost: ~$2
  - Graduation threshold: 500 SOL (~$73K) - higher than Pump.fun
  - Deflationary: Burns 150-200M tokens at graduation
  - Self-custodial wallet with MoonPay integration
  - Best for: Projects wanting to filter out noise
```

### Raydium LaunchLab

Full customization for technical teams.

```
  - Custom bonding curves, supply, vesting schedules
  - No creator revenue sharing
  - Most control available
  - Best for: DeFi projects, complex tokenomics
```

### Decision Framework

| Priority | Choose |
|----------|--------|
| Maximum initial exposure | Pump.fun |
| Ongoing creator revenue | Bags.fm |
| Leverage your X following | Believe |
| Higher quality signal | Moonshot |
| Full tokenomics control | Raydium LaunchLab |

---

## The 30-Minute Post-Graduation Window

This window determines whether your token lives or dies. It is well-documented and real.

### Minute-by-Minute Timeline

```
Minutes 0-5: Detection
  - Automated scanners and snipers detect graduation
  - They check pool depth ($10-15K typical)
  - If thin, a $50 buy moves price 30-40%
  - Most snipers pass on thin pools
  ACTION: Add your own liquidity pool immediately

Minutes 5-15: First Impressions
  - Traders check DexScreener and Birdeye
  - Zero volume + thin depth = they move on
  - First impressions are permanent
  ACTION: Generate visible trading activity

Minutes 15-30: Survival Check
  - If no activity, no depth, no signs of life = dead
  - Telegram goes quiet, momentum evaporates
  - Recovery after this point is nearly impossible
  ACTION: Be visibly active everywhere (CT, TG, DMs)
```

### The Survival Checklist (First 30 Minutes)

```
- [ ] Add own LP at graduation (control price ratio, earn fees)
- [ ] Generate trading activity (show life on DexScreener)
- [ ] Hit 300+ holders in first hour (social proof)
- [ ] Tweet about graduation with chart screenshot
- [ ] Be active in Telegram/community channels
- [ ] Respond to every question immediately
- [ ] Lock LP tokens for 6-12+ months
- [ ] Revoke mint authority and freeze authority
```

---

## Sniper Bot Dynamics

Sniper bots are pervasive. Understanding them is defensive knowledge.

### How They Operate

```
Detection:
  - Detect new tokens and graduation events within seconds
  - Use Jito bundles for priority transaction ordering
  - Track dev wallet buys and copy-trade immediately

What they check:
  - Dev allocation % (skip high allocation)
  - Freeze/mint authority (skip if active)
  - Liquidity depth
  - Holder distribution

Typical settings:
  - Buy amount: 0.1-0.9 SOL
  - Slippage: 5-15%
  - Speed: 0.01-0.29 seconds
```

### Defensive Measures

```
Before launch:
  - [ ] Plan to revoke mint authority immediately
  - [ ] Plan to revoke freeze authority immediately
  - [ ] Keep dev allocation below 10%
  - [ ] Prepare additional SOL for post-graduation LP

At graduation:
  - [ ] Revoke authorities in same block if possible
  - [ ] Add LP immediately (you control the price ratio)
  - [ ] Lock LP tokens (StakePoint or equivalent)
  - [ ] Share token scanner verification publicly

Ongoing:
  - [ ] Transparent on-chain allocations
  - [ ] Public dev wallet address
  - [ ] No unexplained large transfers
```

---

## Token Launch Failure Modes

### The Numbers

```
97%  of meme coins fail within 60 days
60%  dead within 24 hours of launch
86%  of all crypto project failures (2021-2025) occurred in 2025
95%  die within 90 days without staking + locked LP
85%  survive 90 days with both staking AND locked LP
```

### Five Fatal Mistakes

**1. Equating "launch" with "marketing"**
Launch day is the beginning, not the finish line. When the initial pump fades after 72 hours and nothing remains, the token dies.

**2. The "Logo + KOL = Moon" delusion**
A cute logo, 3-5 paid KOL tweets, and a Telegram group with 500 airdrop hunters. This formula produces short-term volume but zero lasting value. It has been replicated millions of times.

**3. Zero cultural resonance**
Most tokens have a logo and a name but lack the cultural DNA that makes people share, remix, and identify with the project. WIF succeeded because of absurdity (dog in hat). PEPE claimed 15+ years of existing internet culture. BONK distributed 40% of supply to actual Solana users.

**4. No post-graduation infrastructure**
Most tokens that graduate lose all trading activity within 48 hours. Not because they are bad - because nobody set up liquidity depth, staking, or trading incentives.

**5. Concentrated holdings / insider manipulation**
Over 98% of Pump.fun tokens show characteristics of rug pulls, wash trading, or manipulation (Solidus Labs). Top 10 wallet concentration, active freeze/mint authority, and dev wallets holding >10% are red flags that experienced traders check instantly.

### Hackathon-Specific Failure Modes

```
Splitting focus:
  Building a product AND managing a token launch simultaneously
  guarantees mediocrity at both.

Premature tokenization:
  Token for a product with zero users.
  Token becomes a substitute for value rather than a representation of it.

No post-hackathon plan:
  Hackathon ends, team disperses, token orphaned.
  Most common scenario for hackathon token launches.

Misaligned incentives:
  If hackathon project is a tool/protocol but token is a meme,
  judges and investors see through this immediately.
```

---

## Timing Strategy

### Optimal Launch Windows

```
Best: Weekdays, 12:00-20:00 UTC
  - US and EU peak hours overlap
  - US market open (14:00-15:00 UTC) = highest crypto trading volume

Risky but less competitive: Weekends
  - Lower overall volume, fewer competing launches

Avoid:
  - Friday evenings (dead zone)
  - During major macro news events or BTC volatility
  - During significant network congestion
  - Dropping without any prior community exposure
```

### The 72-Hour Rule

Tokens either graduate and gain traction within 72 hours or fade permanently. Your pre-launch community must be strong enough to drive sustained buying pressure within this compressed window.

### Hackathon + Token Timing

```
Pre-Hackathon Launch (2-4 weeks before):
  Pros: Time to build community before demo
  Cons: Token may lose momentum; distraction from building
  Risk: Judges may view existing token as "not built during hackathon"

During Hackathon:
  Pros: Leverages hackathon attention
  Cons: Enormous distraction; community management is full-time
  Risk: Both product quality and token survival suffer
  Verdict: Almost never recommended

Post-Hackathon Launch (after demo/winning):
  Pros: Product validated, hackathon win = credibility, full attention
  Cons: Hackathon momentum may have faded
  Verdict: RECOMMENDED if doing both
```

---

## Community Engagement Tactics

### Pre-Launch (2-4 Weeks Before)

```
Cultural Testing (zero cost):
  - Share meme/narrative concepts in communities (no token mention)
  - Track which variations get shared or spark conversation
  - If nothing generates organic engagement, pivot the concept

Core Group Building:
  - Find 50-100 people who genuinely find the project interesting
  - These become distribution nodes at launch
  - Quality > quantity: 500 active > 50,000 airdrop farmers
```

### Launch Window (First 72 Hours)

```
The Coordinated Push:
  - Pre-arrange 5-10 KOLs to post within 2-4 hours (staggered)
  - Core community ready with 20-30 meme variations
  - Goal: "everyone's talking about this" atmosphere within 24 hours

Daily Activity:
  - 10 rough memes beat 1 polished video
  - Retweet and celebrate community-created content
  - Jump on trending topics with relevant content
  - Be present in all channels continuously
```

### Post-72-Hour Survival

```
Identity Over Price:
  - If relying on "look how much we pumped" past 72 hours, you have lost
  - Shift to identity narrative: insider language, community-exclusive terminology

Participation Rituals:
  - Weekly meme contests or community AMAs
  - Let community vote on project matters
  - Host regular X Spaces

Utility Layer (Critical):
  - Staking + locked LP = 85% 90-day survival rate
  - Neither staking nor locked LP = 5% 90-day survival rate
  - The gap is not subtle
```

---

## Full Launch Checklist

### T-minus 2 Weeks

```
- [ ] Test narrative concept in communities (no token mention)
- [ ] Build core group of 50-100 genuine supporters
- [ ] Pre-arrange KOL partnerships with staggered posting schedule
- [ ] Prepare 20-30 meme/content variations for launch day
- [ ] Have additional SOL ready for post-graduation liquidity
- [ ] Choose launchpad (Pump.fun, Bags.fm, Believe, Moonshot, LaunchLab)
- [ ] Prepare token scanner verification data
- [ ] Review jurisdiction-specific legal requirements
```

### Launch Day

```
- [ ] Launch during weekday, 12:00-20:00 UTC
- [ ] Revoke mint authority and freeze authority immediately
- [ ] At graduation (minute 0-5): add additional LP
- [ ] At minute 5-15: ensure trading activity visible on DexScreener
- [ ] At minute 15-30: be visibly active on socials
- [ ] Lock LP tokens for 6-12+ months
- [ ] Share safety verification (token scanner results)
- [ ] Begin coordinated KOL push
```

### First 72 Hours

```
- [ ] Community meme/content deployment across all channels
- [ ] Daily updates, AMAs, engagement
- [ ] Set up staking pool (if applicable)
- [ ] Transparent communication about roadmap
- [ ] Respond to all community questions within minutes
- [ ] Monitor on-chain metrics (holders, volume, LP depth)
```

### Post 72 Hours

```
- [ ] Shift from "new discovery" to "community identity"
- [ ] Establish weekly engagement rituals
- [ ] Continue utility development
- [ ] Keep adding liquidity depth
- [ ] Deliver on promises (the easiest way to die is to overpromise)
```

---

## Regulatory Environment (February 2026)

Compliance is now a competitive advantage. Key regulations:

```
United States:
  - SEC enforcement actions against unregistered airdrop distributions
  - IRS treats every airdropped token as taxable ordinary income
  - Wash trading during airdrops can trigger CFTC enforcement
  - Clarity Act and Genius Act creating stricter frameworks
  - US users increasingly excluded from major airdrops

Europe:
  - MiCA (Markets in Crypto-Assets) regulation in effect
  - Clear licensing requirements for token issuers

General:
  - Legal review is no longer optional - it is prerequisite
  - Jurisdiction selection matters: some are hostile, others provide clarity
  - "Compliance has become a competitive advantage" (ICODA, Oct 2025)
```

**If your protocol works without a token, seriously consider not launching one.**

---

## Pump.fun Build in Public Hackathon Model

A new paradigm combining token launch with product building (launched January 2026).

```
Structure:
  - $3M total pool, 12 winners at $250K each
  - Investment at $10M valuation
  - No judges - market traction and visible execution determine winners
  - Pump Fund (pump.fun's investment arm) makes final decisions

Requirements:
  - Launch token on pump.fun
  - Retain minimum 10% supply (costs ~3.15 SOL)
  - Build in public for 30 days
  - Ship visible updates daily

First winner: zauth (Feb 14, 2026)
  - AI trust infrastructure for autonomous agents
  - Received $250K from Pump Fund
  - Demonstrated: launch token day 1, build visibly, let market signal quality
```

### Best Practices from the Hackathon

```
- Buy 20-50% of own supply at launch (10% minimum for eligibility)
- Lock tokens via Streamflow or Jupiter Lock (long-term signal)
- Use pump.fun live streams to show real work
- Ship daily, communicate daily
- Actively listen to holder/user feedback
- Collaborate with other founders in the ecosystem
- Be precise about what exists vs what is planned
```

---

## Cost Structure

| Item | Pump.fun Route | Custom Contract Route |
|------|---------------|----------------------|
| Token creation | Near-free (gas only) | $6K-$12K |
| Initial purchase (20% supply) | ~6.3 SOL (~$570) | N/A |
| LP capital | Built into bonding curve | $10K-$100K |
| Website | Optional (pump.fun page) | $3K-$12K |
| Anti-bot/bundling | Not applicable | $5K-$15K |
| **Total minimum** | **~$600 + gas** | **$20K-$40K** |

For hackathon builders, pump.fun's near-zero cost removes financial barriers. The investment is time and reputation, not capital.

---

## Simple Tokenomics for Product-Backed Tokens

### Models That Work (2025-2026 Data)

**Revenue-sharing / Buyback (strongest performer):**
- Protocol revenue buys back or burns tokens
- Hyperliquid: $716M in buybacks, leading all 2025
- Pump.fun: $45M/month distributed to PUMP holders
- Creates direct linkage between product usage and token value

**Access/Utility Token:**
- Token required to access or use the product
- Works when product has genuine, recurring demand
- Failure mode: no users = no floor

### For Hackathon-Timeline Products

```
The simplest viable model:
  - Fixed supply (1B tokens, enforced by pump.fun)
  - Creator buys 20-50% at launch for team/development reserve
  - Lock team tokens via Streamflow or Jupiter Lock
  - Revenue from product -> buy back tokens (once revenue exists)
  - No complex mechanisms at launch - add utility as product matures

What to avoid:
  - Promising specific token utility before the product exists
  - Complex vesting or emission schedules you cannot manage solo
  - Any mechanism requiring ongoing manual intervention you cannot sustain
```

### The Uncomfortable Truths

```
1. 0.63% graduation rate means your token will almost certainly die.
   Plan for this. The token is an experiment, not your company's equity.

2. 85% of all 2025 tokens are underwater - including VC-backed tokens
   with teams of 50+ people.

3. The single strongest predictor of survival is rapid early momentum -
   concentrated buying in few transactions.

4. Product-market fit determines everything post-graduation.
   No tokenomics sophistication compensates for lack of product.

5. 92% of tokens experience pump-and-dump dynamics.
   Build psychology and communication strategy around this reality.
```
