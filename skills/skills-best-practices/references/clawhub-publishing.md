# Publishing to ClawHub

ClawHub ([clawhub.ai](https://clawhub.ai)) is a public registry for Agent Skills. It extends Anthropic's base skill spec with runtime metadata (`metadata.openclaw`), an automatic moderation audit (SkillSpector + VirusTotal + risk analysis), and a CLI/API for publishing. This is the field guide for getting skills past moderation on the first try.

Sources of truth: [skill-format.md](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md), [security-audits.md](https://github.com/openclaw/clawhub/blob/main/docs/security-audits.md), [moderation.md](https://github.com/openclaw/clawhub/blob/main/docs/moderation.md), [cli.md](https://github.com/openclaw/clawhub/blob/main/docs/cli.md).

## What ClawHub adds to the Anthropic spec

| Concept | Anthropic spec | ClawHub addition |
|---|---|---|
| Frontmatter | `name`, `description`, optional `metadata: dict[str,str]` | `metadata.openclaw.*` runtime declarations |
| Distribution | Manual (zip / file path) | Versioned registry, semver tags, search |
| Trust | None enforced | 3-scanner moderation pipeline |
| Slug | Local filename | Globally unique slug (URL-safe; 30-day hold after delete) |
| License | Author choice | All skills MIT-0 (auto-applied) |

## `metadata.openclaw` schema

Use the **YAML nested form** (not the JSON-blob form). `metadata.openclaw` is the canonical key; `metadata.clawdbot` and `metadata.clawdis` are aliases - skip them.

```yaml
---
name: my-skill
description: One-line summary with triggers.
metadata:
  version: "0.1.0"
  openclaw:
    homepage: https://github.com/owner/repo/tree/main/skills/my-skill
    primaryEnv: MY_API_KEY
    requires:
      bins: [curl]
      env: [MY_API_KEY]
      config: [~/.config/my-skill/config.json]
    envVars:
      - name: MY_API_KEY
        required: true
        description: Primary credential for the upstream service.
      - name: MY_OPTIONAL_FLAG
        required: false
        description: Toggles experimental behavior.
    emoji: "🔌"
    os: [darwin, linux]
---
```

Field reference:

| Field | Type | Purpose |
|---|---|---|
| `requires.env` | `string[]` | Hard-required env vars. Skill cannot run without these. |
| `requires.bins` | `string[]` | Binaries that must all be on PATH. |
| `requires.anyBins` | `string[]` | At least one of these binaries must be present. |
| `requires.config` | `string[]` | Config file paths that must exist/be truthy. |
| `envVars[]` | `{name, required?, description?}` | Per-variable metadata. **Use this for optional env vars** with `required: false`. |
| `primaryEnv` | `string` | Main credential. Must also appear in `requires.env` or `envVars`. |
| `homepage` | `string` | Source URL. Raises trust score; ClawScan flags missing homepage. |
| `emoji` | `string` | Single emoji for UI display. |
| `os` | `string[]` | OS filter (`darwin`, `linux`, etc.). |
| `always` | `boolean` | If true, skill is always active. Use with caution - flagged for review. |
| `skillKey` | `string` | Override invocation key (rarely needed). |
| `install[]` | `array` | Auto-install hints (`brew`, `node`, `go`, `uv`). |
| `install[].id/label/tap` | `string` | Optional per-spec id, display label, and Homebrew tap. |
| `nix` | `object` | Nix plugin spec (see ClawHub README). |
| `config` | `object` | Clawdbot config spec (`requiredEnv` / `stateDirs` / `example`). |
| `links` | `object` | `{homepage, repository, documentation, changelog}` URLs. |
| `author` | `string` | Author handle or name. |
| `cliHelp` | `string` | CLI help text surfaced in the registry. |
| `dependencies[]` | `array` | `{name, type, version?, url?, repository?}`; `type` in pip/npm/brew/go/cargo/apt/other. |

**Critical rule**: required env vars go under `requires.env`; optional/integration env vars go under `envVars` with `required: false`. Putting optional vars in `requires.env` will make ClawHub gate the skill behind credentials it doesn't actually need; mixing them up flags as metadata mismatch.

## Slugs and display names

- Slug regex: `^[a-z0-9](?:(?!--)[a-z0-9-])*[a-z0-9]$` - lowercase kebab-case, 3-96 chars, must start and end with a letter or digit, no consecutive hyphens.
- Reserved slugs (`official`, `clawhub`, `admin`, `api`, ...) and protected affixes (`openclaw-*`, `*-official`, `*-verified`, ...) are rejected to block route clashes and brand squatting.
- Default slug = folder name. Override at publish with `--slug`.
- Renaming: `clawhub skill rename <old> <new>` keeps the old slug as a redirect alias.
- Display name is set at publish via `--name`. Convention in this repo: **display name == slug** (set automatically by `scripts/prepare_skill_release.py`).
- Slugs are globally unique across all of ClawHub. An owner soft-delete reserves the slug for 30 days, after which it frees up; if your folder name is taken, you'll need a `--slug` override.

## Install specs

Declare third-party tooling under `metadata.openclaw.install`:

```yaml
install:
  - kind: brew
    formula: jq
    bins: [jq]
  - kind: node
    package: typescript@5
    bins: [tsc]
  - kind: go
    module: github.com/user/tool@latest
    bins: [tool]
  - kind: uv
    package: ruff==0.15.12
    bins: [ruff]
```

Supported kinds: `brew`, `node`, `go`, `uv`. Validation: no shell metacharacters in package names.

## Moderation pipeline

Every publish runs a moderation audit that combines three components; the worst signal wins.

| Component | Emits | What it catches |
|---|---|---|
| **SkillSpector** | agentic-risk findings | LLM-driven review of skill behavior and intent. |
| **VirusTotal** | telemetry only (no reason code) | URL/file content reputation (known malware signatures, bad domains). |
| **Risk analysis (ClawScan)** | `review.*` / `suspicious.*` / `malicious.*` reason codes | Context-aware semantic review. Flags metadata-vs-runtime mismatch, capability overreach, undeclared credentials, internal contradictions. |

Static analysis runs too, but its signals are **internal context for the review, not a standalone public verdict or install-blocking result**. The LLM review emits `review.llm_review` (a `review.` tier, distinct from `suspicious`). The overall verdict is derived from code prefixes: any `malicious.*` => malicious, any `suspicious.*` => suspicious, only `review.*` => a "Review" tier. Risk analysis uses the [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/) as a lens (prompt injection, tool misuse, credential exposure, unsafe execution, context poisoning, excessive agency).

To inspect: `curl -H "Authorization: Bearer <token>" https://clawhub.ai/api/v1/skills/<slug>` returns the `moderation` block with `verdict` (`clean` / `suspicious` / `malicious`), `reasonCodes[]`, `summary`, and `engineVersion` (currently `v2.4.26`). Public audit status is one of `Pass` / `Review` / `Warn` / `Malicious` / `Pending` / `Error`, with a risk level of `Low` / `Medium` / `High`.

## Reason codes catalog

The moderation engine defines ~26 reason codes (source of truth: [`convex/lib/moderationReasonCodes.ts`](https://github.com/openclaw/clawhub/blob/main/convex/lib/moderationReasonCodes.ts)). The table below is a curated subset of the ones authors hit most; grep the source enum for the full list.

| Code | Trigger | Fix |
|---|---|---|
| `review.llm_review` | Metadata-runtime mismatch, capability overreach, contradictions (surfaces as the "Review" tier, not "suspicious") | Declare every env / bin / config referenced in the body. Add `homepage`. Resolve flag contradictions (see below). |
| `suspicious.exposed_secret_literal` | Long hex (`0x[a-f0-9]{40,}`), JWT-shaped strings, base64 blobs | Replace with placeholders (`<USDC_MAINNET>`) + a single canonical address/key reference table. |
| `suspicious.destructive_delete_command` | Literal `rm -rf` (even in pedagogical "don't do this" context) | Reword ("force-recursive removal") or break the literal with markup. |
| `suspicious.potential_exfiltration` | Skill packages user data and sends it off-host | Document the destination model/endpoint and data-handling policy. May be intrinsic to design. |
| `suspicious.generated_source_template_injection` | `${VAR}` placeholders in code blocks | Declare those env vars in `metadata.openclaw`. Often a metadata-mismatch echo. |
| `suspicious.dangerous_exec` / `suspicious.dynamic_code_execution` | Shelling out or eval-ing dynamically built code | Call fixed, auditable commands; avoid runtime code generation. |
| `suspicious.obfuscated_code` | Base64/hex-encoded or minified payloads | Ship readable source; never bundle encoded blobs. |
| `suspicious.install_untrusted_source` / `suspicious.credential_exposure_instructions` / `suspicious.prompt_injection_instructions` | Untrusted install source, instructions to expose credentials, or embedded injection text | Remove the instruction; declare install specs via `metadata.openclaw.install`. |

Only `suspicious.env_credential_access` is externally self-clearable; the rest require a fixed re-publish.

**Hard-block** codes (`malicious.install_terminal_payload`, `malicious.crypto_mining`, `malicious.known_blocked_signature`) auto-hide the skill and place the uploader in manual moderation. The most common is `malicious.install_terminal_payload`: install instructions that tell users to paste obfuscated shell payloads (e.g., base64-decoded `curl | bash`). Never include these.

## Capability tags (auto-derived)

ClawHub computes 9 capability tags at publish time by running deterministic regex matchers over the lowercased concatenation of slug + display name + summary + frontmatter (JSON-stringified) + README + every text file in the bundle. Source of truth: [`convex/lib/skillCapabilityTags.ts`](https://github.com/openclaw/clawhub/blob/main/convex/lib/skillCapabilityTags.ts).

These tags are **not author-declared**. The only way to drop a tag is to remove every word in the bundle that triggers its regex.

| Tag | Trigger word families |
|---|---|
| `crypto` | `crypto`, `blockchain`, `defi`, `on-chain`, `wallet`, `private key`, `erc-20`, `usdc`, `eth/ethereum`, `bitcoin/btc`, `base network`, `arbitrum`, `optimism`, `polygon`, `avalanche`, `solana`, `aave`, `token balance`, `bridge`, `liquidity`, `ens`, `x402`, contextual `defi/token/coin/nft swap` patterns |
| `financial-authority` | No regex of its own - **derived** when `can-make-purchases` or `can-sign-transactions` is set (see Auto-implications) |
| `requires-wallet` | `private key`, `wallet`, `walletClient`, `sendTransaction`, `mnemonic`, `seed phrase`, `configured wallet`, `signer`, `eip-712` |
| `can-make-purchases` | `paid automatically`, `micropayments`, `process/accept/collect payments`, `make/send/authorize payments`, `pay invoices/bills/vendors`, `payment processing`, `charge cards/customers`, `buy {credits/tokens/coins/nft/subscription/plan}`, `buy/order products after user approval`, `payment checkout`, `one-click checkout` |
| `can-sign-transactions` | `sign (and submit/send/broadcast/authorize/approve) transaction(s)`, `sendTransaction`, `approval_required`, `on-chain tx/transaction`, `execute transaction`, `broadcast transaction`, `walletClient.sendTransaction` (database/SQL/internal/workflow transactions are excluded) |
| `requires-paid-service` | `payment required`, `paid subscription/plan/api required`, `requires a pro/premium/billing subscription`, `pay per call`, `costs $N`, `charged per call/request`, `account top-up/recharge`, `402 payment required` + `insufficient balance`. Negations (`no payments required`, `never requires a subscription`) are stripped before matching |
| `requires-oauth-token` | `oauth`, `oauth 2.0`, `access token`, `refresh token`, `bearer token`, `tweet.write` |
| `requires-sensitive-credentials` | `api key`/`api_key`/`api-key`, `access/refresh/bearer token`, `session/auth cookie(s)`, `private key`, `mnemonic`, `seed phrase`, `signer` |
| `posts-externally` | `post (a/this) tweet`, `reply to tweet`, `quote tweet`, `post to x/twitter`, `twitter-post`, `publish post` |

**Auto-implications** (set after the regex pass):
- `can-make-purchases` OR `can-sign-transactions` → adds `financial-authority`
- `can-sign-transactions` AND `crypto` → adds `requires-wallet`
- `requires-wallet` OR `can-sign-transactions` OR `requires-oauth-token` → adds `requires-sensitive-credentials`

Purchase or transaction-signing authority on its own no longer derives `crypto` or `requires-wallet`; non-crypto financial skills get `financial-authority` instead.

**Why this matters**: ClawScan (the LLM scanner) reads the capability tags and flags `suspicious` when a tag is set but the skill's stated purpose doesn't justify it (e.g. a fact-check skill with `can-make-purchases`). The fix is **always** content-side: find the trigger word, remove or rephrase it. Defensive scoping language (e.g., "this skill does NOT make payments") usually backfires - it adds the very trigger words it tries to disclaim.

**False-positive appeal**: when a tag is genuinely incorrect (e.g. `display=swap` matching the `\bswap\b` crypto regex) and the trigger word can't be rephrased, file an issue at [openclaw/clawhub](https://github.com/openclaw/clawhub/issues) - maintainers tighten regex patterns over time (see PR #1857 for an example fix).

## Author-declarable flags

`disable-model-invocation: true` (top-level frontmatter, not under `metadata`):
- Stops Claude from auto-invoking the skill based on prompt content. Skill only fires on explicit slash command.
- Use for explicit-invocation skills (e.g., `/review`, `/polish`).
- **Don't combine** with internal `Agent(model: "opus")` overrides in the skill body - that contradiction triggers high-confidence suspicious. Subagents inherit the parent's model anyway.

`always: true` (under `metadata.openclaw`): skill loads at every session. Combine with `homepage` and explicit credential declarations or it'll flag.

## Publishing constraints

- 50 MB total bundle size; 10 MB per-file cap.
- Text-based files only (no binaries).
- GitHub account must be ≥ 14 days old.
- All publishes are MIT-0; no per-skill license overrides.
- Semver versions are immutable; tags (`latest`) are mutable pointers.
- No paid skills, no per-skill pricing, no paywalls.
- Publishing 5 *new* skills/hour (rate limit on first-time slugs only; updates aren't capped).

## CLI cheat-sheet

The canonical publish command is `clawhub skill publish <path>` (bare `publish <path>` is a legacy alias). Its documented flags are `--version`, `--dry-run`, `--json`, `--owner`, and `--migrate-owner`; new skills default to `1.0.0` and changed skills auto-bump to the next patch. The older `--slug` / `--name` / `--changelog` / `--tags` flags are no longer in the documented CLI surface - run `clawhub skill publish --help` before relying on them (this repo's release pipeline still passes some via `scripts/publish_release.py`; verify against your installed CLI version).

```bash
# Publish (auto-versions; --dry-run to preview)
clawhub skill publish ./skills/my-skill --dry-run
clawhub skill publish ./skills/my-skill
clawhub skill publish ./skills/my-skill --version 2.0.0

# Inspect (owner-visible moderation diagnostics when logged in)
clawhub inspect @owner/my-skill --json

# Scan an existing version + download the stored report (works on blocked/hidden versions)
clawhub scan --slug my-skill
clawhub scan download my-skill --version 1.2.3   # report ZIP: clawscan.json, skillspector.json, static-analysis.json, virustotal.json

# Soft-delete / restore (owner reversible; soft-delete holds the slug 30 days)
clawhub delete my-skill
clawhub undelete my-skill

# Rename (preserves redirect from old slug)
clawhub skill rename my-skill my-new-skill

# Sync all changed local skills (one-way publish)
clawhub sync --all --bump patch
```

For a version blocked at moderation, `clawhub scan download <slug> --version <v>` retrieves the stored scan report so you can see exactly which reason codes fired before re-publishing a fix.

Direct moderation API (most useful for debugging suspicious flags):

```bash
TOKEN="$(jq -r .token "$HOME/Library/Application Support/clawhub/config.json")"
curl -sS -H "Authorization: Bearer $TOKEN" \
  https://clawhub.ai/api/v1/skills/<slug> | jq .moderation
```

## Pre-publish checklist

- [ ] Frontmatter `name` matches folder name.
- [ ] `description` ≤ 1024 chars; includes trigger phrases.
- [ ] Every env var, binary, and config path referenced in SKILL.md or references is declared in `metadata.openclaw`.
- [ ] Optional env vars use `envVars` with `required: false`, not `requires.env`.
- [ ] `homepage` set.
- [ ] `metadata.version` bumped (semver, never reused).
- [ ] No instruction text contains literal `curl | bash` with base64 (hard-block).
- [ ] No internal `Agent(model: "opus")` calls in the skill body if `disable-model-invocation: true`.
- [ ] No long secret-shaped literals; addresses/keys go in a single canonical reference table with placeholders inline.
- [ ] `LICENSE.txt` present (auto-added by ClawHub publish; required for external bundles).
- [ ] Run `just check` (or equivalent linter) green.
