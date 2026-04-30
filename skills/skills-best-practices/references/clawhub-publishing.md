# Publishing to ClawHub

ClawHub ([clawhub.ai](https://clawhub.ai)) is a public registry for Agent Skills. It extends Anthropic's base skill spec with runtime metadata (`metadata.openclaw`), automatic moderation (3 scanners), and a CLI/API for publishing. This is the field guide for getting skills past moderation on the first try.

Sources of truth: [openclaw/clawhub/docs/skill-format.md](https://github.com/openclaw/clawhub/blob/main/docs/skill-format.md), [security.md](https://github.com/openclaw/clawhub/blob/main/docs/security.md), [cli.md](https://github.com/openclaw/clawhub/blob/main/docs/cli.md), [spec.md](https://github.com/openclaw/clawhub/blob/main/docs/spec.md).

## What ClawHub adds to the Anthropic spec

| Concept | Anthropic spec | ClawHub addition |
|---|---|---|
| Frontmatter | `name`, `description`, optional `metadata: dict[str,str]` | `metadata.openclaw.*` runtime declarations |
| Distribution | Manual (zip / file path) | Versioned registry, semver tags, search |
| Trust | None enforced | 3-scanner moderation pipeline |
| Slug | Local filename | Globally unique slug (URL-safe, never reused) |
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
| `install[]` | `array` | Auto-install hints (`brew`, `node`, `go`, `uv`, `download`). |

**Critical rule**: required env vars go under `requires.env`; optional/integration env vars go under `envVars` with `required: false`. Putting optional vars in `requires.env` will make ClawHub gate the skill behind credentials it doesn't actually need; mixing them up flags as metadata mismatch.

## Slugs and display names

- Slug regex: `^[a-z0-9][a-z0-9-]*$`. Lowercase, kebab-case.
- Default slug = folder name. Override at publish with `--slug`.
- Renaming: `clawhub skill rename <old> <new>` keeps the old slug as a redirect alias.
- Display name is set at publish via `--name`. Convention in this repo: **display name == slug** (set automatically by `scripts/prepare_skill_release.py`).
- Slugs are globally unique across all of ClawHub. If your folder name is taken, you'll need a `--slug` override.

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
  - kind: download
    url: https://example.com/binary.tar.gz
    archive: tar.gz
    bins: [binary]
```

Validation: no shell metacharacters in package names; HTTPS-only URLs; no `..` in paths.

## Moderation pipeline

Every publish triggers three scans. Each contributes a verdict; the worst wins.

| Scanner | Reason code prefix | What it catches |
|---|---|---|
| **VirusTotal** | `vt_*` | URL/file content reputation (known malware signatures, bad domains). |
| **ClawScan** (LLM) | `llm_suspicious` | Context-aware semantic review (gpt-5-mini). Flags metadata-vs-runtime mismatch, capability overreach, undeclared credentials, internal contradictions. |
| **Static analysis** | specific codes (see below) | Pattern matching for risky literals. |

ClawScan's review dimensions: `Purpose & Capability`, `Instruction Scope`, `Install Mechanism`, `Credentials`, `Persistence & Privilege`. Each can be `ok` / `note` / `concern`.

To inspect: `curl -H "Authorization: Bearer <token>" https://clawhub.ai/api/v1/skills/<slug>` returns the `moderation` block with `verdict` (`clean` / `suspicious` / `malicious`), `reasonCodes[]`, `summary`, `engineVersion`.

## Reason codes catalog

| Code | Trigger | Fix |
|---|---|---|
| `suspicious.llm_suspicious` | Metadata-runtime mismatch, capability overreach, contradictions | Declare every env / bin / config referenced in the body. Add `homepage`. Resolve flag contradictions (see below). |
| `suspicious.exposed_secret_literal` | Long hex (`0x[a-f0-9]{40,}`), JWT-shaped strings, base64 blobs | Replace with placeholders (`<USDC_MAINNET>`) + a single canonical address/key reference table. |
| `suspicious.destructive_delete_command` | Literal `rm -rf` (even in pedagogical "don't do this" context) | Reword ("force-recursive removal") or break the literal with markup. |
| `suspicious.potential_exfiltration` | Skill packages user data and sends it off-host | Document the destination model/endpoint and data-handling policy. May be intrinsic to design. |
| `suspicious.generated_source_template_injection` | `${VAR}` placeholders in code blocks | Declare those env vars in `metadata.openclaw`. Often a metadata-mismatch echo. |
| `suspicious.vt_suspicious` | URL or filename matched VT signature | Grep all URLs/filenames in the bundle; submit each to VT; replace the offender. |

**Hard-block** (auto-hides skill, places uploader in manual moderation): install instructions that tell users to paste obfuscated shell payloads (e.g., base64-decoded `curl | bash`). Never include these.

## Capability tags (auto-derived)

ClawHub computes 7 capability tags at publish time by running deterministic regex matchers over the lowercased concatenation of slug + display name + summary + frontmatter (JSON-stringified) + README + every text file in the bundle. Source of truth: [`convex/lib/skillCapabilityTags.ts`](https://github.com/openclaw/clawhub/blob/main/convex/lib/skillCapabilityTags.ts).

These tags are **not author-declared**. The only way to drop a tag is to remove every word in the bundle that triggers its regex.

| Tag | Trigger word families |
|---|---|
| `crypto` | `crypto`, `blockchain`, `defi`, `on-chain`, `wallet`, `private key`, `erc20`, `usdc`, `eth/ethereum`, `base network`, `arbitrum`, `optimism`, `polygon`, `avalanche`, `solana`, `aave`, `token balance`, `bridge`, `liquidity`, `ens`, `x402`, contextual `defi/token/coin/nft swap` patterns |
| `requires-wallet` | `private key`, `wallet`, `mnemonic`, `seed phrase`, `configured wallet`, `signer`, `eip-712` |
| `can-make-purchases` | `payment(s)`, `paid automatically`, `pay per call`, `micropayments`, `payment required`, `costs $N`, `charged`, `purchase`, `buy {credits/tokens/coins/nft/subscription/plan}`, `payment checkout`, `one-click checkout` |
| `can-sign-transactions` | `sign(ing) (and submit/send/broadcast) transaction(s)`, `sendTransaction`, `approval_required`, `on-chain tx/transaction`, `execute transaction`, `broadcast transaction`, `walletClient.sendTransaction` |
| `requires-oauth-token` | `oauth`, `oauth 2.0`, `access token`, `refresh token`, `bearer token`, `tweet.write` |
| `requires-sensitive-credentials` | `api key`/`api_key`/`api-key`, `access/refresh/bearer token`, `session/auth cookie(s)`, `private key`, `mnemonic`, `seed phrase`, `signer` |
| `posts-externally` | `post (a/this) tweet`, `reply to tweet`, `quote tweet`, `post to x/twitter`, `twitter-post`, `publish post` |

**Auto-implications** (set after the regex pass):
- `can-sign-transactions` OR `can-make-purchases` → adds `crypto`
- `can-sign-transactions` → adds `requires-wallet`
- `requires-wallet` OR `can-sign-transactions` OR `requires-oauth-token` → adds `requires-sensitive-credentials`

**Why this matters**: ClawScan (the LLM scanner) reads the capability tags and flags `suspicious` when a tag is set but the skill's stated purpose doesn't justify it (e.g. a fact-check skill with `can-make-purchases`). The fix is **always** content-side: find the trigger word, remove or rephrase it. Defensive scoping language (e.g., "this skill does NOT make payments") usually backfires - it adds the very trigger words it tries to disclaim.

**False-positive appeal**: when a tag is genuinely incorrect (e.g. `display=swap` matching the `\bswap\b` crypto regex) and the trigger word can't be rephrased, file an issue at [openclaw/clawhub](https://github.com/openclaw/clawhub/issues) - maintainers tighten regex patterns over time (see PR #1857 for an example fix).

## Author-declarable flags

`disable-model-invocation: true` (top-level frontmatter, not under `metadata`):
- Stops Claude from auto-invoking the skill based on prompt content. Skill only fires on explicit slash command.
- Use for explicit-invocation skills (e.g., `/review`, `/polish`).
- **Don't combine** with internal `Agent(model: "opus")` overrides in the skill body - that contradiction triggers high-confidence suspicious. Subagents inherit the parent's model anyway.

`always: true` (under `metadata.openclaw`): skill loads at every session. Combine with `homepage` and explicit credential declarations or it'll flag.

## Publishing constraints

- 50 MB total bundle size.
- Text-based files only (no binaries).
- GitHub account must be ≥ 14 days old.
- All publishes are MIT-0; no per-skill license overrides.
- Semver versions are immutable; tags (`latest`) are mutable pointers.
- No paid skills, no per-skill pricing, no paywalls.
- Publishing 5 *new* skills/hour (rate limit on first-time slugs only; updates aren't capped).

## CLI cheat-sheet

```bash
# Publish (requires existing slug for first-time + --version semver)
clawhub publish ./skills/my-skill \
  --slug my-skill \
  --name my-skill \
  --version 0.1.0 \
  --changelog "Initial release." \
  --tags latest

# Inspect (owner-visible moderation diagnostics when logged in)
clawhub inspect my-skill --json

# Soft-delete / restore (owner reversible)
clawhub delete my-skill
clawhub undelete my-skill

# Rename (preserves redirect from old slug)
clawhub skill rename my-skill my-new-skill

# Sync all changed local skills
clawhub sync --bump patch --tags latest
```

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
