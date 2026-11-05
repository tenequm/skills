# Skills

Agent skills for founders and developers, published to [ClawHub](https://clawhub.ai/tenequm/skills).

Each skill is a folder under `skills/<name>/` with a `SKILL.md` plus optional `references/`. Retired skills live in `archive/` and are no longer published.

## Table of Contents

- [Install](#install)
- [Skill Catalog](#skill-catalog)
- [Releases](#releases)
- [Contributing](#contributing)
- [License](#license)

## Install

```bash
# From ClawHub
clawhub install @tenequm/<skill-name>

# Or straight from this repository
npx skills add tenequm/skills@<skill-name>
```

## Skill Catalog

<!-- GENERATED_SKILLS_TABLE_START -->
| Skill | Version | ClawHub | Description |
|-------|---------|---------|-------------|
| `acpx-faq` | 0.11.0 | [page](https://clawhub.ai/tenequm/skills/acpx-faq) | Run coding agents (codex, claude, agy) through the acpx ACP CLI - one-shot dispatch into named sessions you can watch live. Use before launching or prompting a subagent, or when a command fails, a session is missing, or a prompt is lost. |
| `founder-playbook` | 0.1.7 | [page](https://clawhub.ai/tenequm/skills/founder-playbook) | Decision validation and thinking frameworks for founders. Use to pressure-test a decision, validate next steps, or sanity-check an approach - "should I", "help me think through", "what am I missing". Covers fundraising, customers, runway. |
| `ghostwriter` | 0.1.3 | [page](https://clawhub.ai/tenequm/skills/ghostwriter) | Write content by interviewing the user instead of drafting - extract their material through questions, then assemble the piece from their own words. Use when the user needs to write something for an audience or mentions "ghostwriter". |
| `go-dev` | 0.6.1 | [page](https://clawhub.ai/tenequm/skills/go-dev) | Opinionated Go setup with golangci-lint v2, gofumpt, gotestsum, golang-migrate, and just. Use when starting a Go project, configuring lint, format, test, coverage or CI, writing a Justfile, wiring migrations, or leaving a Makefile workflow. |
| `grill-me` | 0.1.4 | [page](https://clawhub.ai/tenequm/skills/grill-me) | Interview the user relentlessly about a plan or design until reaching shared understanding, resolving each branch of the decision tree. Use when user wants to stress-test a plan, get grilled on their design, or mentions "grill me". |
| `i-have-adhd` | 0.1.1 | [page](https://clawhub.ai/tenequm/skills/i-have-adhd) | Shape output for a reader with ADHD: lead with the next action, number multi-step work, restate state, suppress tangents, make wins visible. Use when the user types /i-have-adhd or asks for ADHD mode; stays on until "stop adhd mode". |
| `lance-format` | 0.22.0 | [page](https://clawhub.ai/tenequm/skills/lance-format) | Deep reference for Lance v15 columnar format, its Rust crates, and pylance - file encodings, table format, indexes, schema evolution, time travel. Use when building on the Lance crates or reading .lance datasets, not the LanceDB product. |
| `mcp-best-practices` | 1.3.1 | [page](https://clawhub.ai/tenequm/skills/mcp-best-practices) | Build, harden, and debug production MCP servers with the TypeScript SDK. Use when writing or reviewing an MCP server - transports, tool schemas, errors, OAuth, token bloat, SDK migrations, MCP Apps, Registry. Assumes a server already exists. |
| `okf-project-knowledge-base` | 0.3.1 | [page](https://clawhub.ai/tenequm/skills/okf-project-knowledge-base) | Durable project knowledge as Git-native OKF bundles (docs/knowledge/, one concept per file, with provenance and trust tiers). Use to record a decision, finding, or rule that must outlive the session. Not session state or agent instructions. |
| `polish-new` | 0.1.3 | [page](https://clawhub.ai/tenequm/skills/polish-new) | Pre-release code review that converges - parallel review agents sized to the diff, findings validated against evidence in a run ledger, fixes on approval, then re-reviews its own fixes until a round warrants no edits. Run on /polish-new. |
| `polish` | 3.1.1 | [page](https://clawhub.ai/tenequm/skills/polish) | Pre-release code review - lint and type checks, parallel review agents (cleanliness, design, efficiency, side-effect gating), findings validated, fixes on approval. Reviews a GitHub PR when given one. Run before committing, pushing, or on a PR. |
| `pre-compact` | 0.1.5 | [page](https://clawhub.ai/tenequm/skills/pre-compact) | Prepare the session for context compaction - write a handoff file a fresh session can continue from, propose updates to the project's durable docs, apply them on approval or with `auto`. Use before compacting or clearing context, or on "pre-compact". |
| `python-dev` | 0.3.1 | [page](https://clawhub.ai/tenequm/skills/python-dev) | Opinionated Python development setup with uv, ty, ruff, pytest, lefthook, and just. Use when creating a new Python project, writing or fixing pyproject.toml, or configuring linting, formatting, type checking, testing, git hooks, or CI. |
| `reset-context-contamination` | 0.1.5 | [page](https://clawhub.ai/tenequm/skills/reset-context-contamination) | Discards this thread's accumulated drafts and framings and re-derives the task from a clean problem statement. Use when the user says the thread is contaminated, the conversation is going in circles, or that they want a fresh take. |
| `rust-dev` | 0.9.0 | [page](https://clawhub.ai/tenequm/skills/rust-dev) | Day-1 guide to building well in Rust - ownership, errors as values, String vs &str, Box/Rc/Arc, anyhow vs thiserror, and a crate shortlist (tokio, serde, axum, sqlx). Use when starting a Rust project, fighting the borrow checker, or picking crates. |
| `skills-best-practices` | 0.9.1 | [page](https://clawhub.ai/tenequm/skills/skills-best-practices) | Opinionated best practices for building Agent Skills - SKILL.md structure, frontmatter, description writing, progressive disclosure, testing, distribution. Use when creating or reviewing a skill, or debugging why one will not trigger. |
| `standard-readme` | 0.1.6 | [page](https://clawhub.ai/tenequm/skills/standard-readme) | Writes or audits READMEs against the Standard Readme spec. Use whenever the user asks to create, rewrite, improve, audit, or fix a README, or asks about README quality or structure - even if they never mention "standard readme". |
| `swift-dev` | 0.3.1 | [page](https://clawhub.ai/tenequm/skills/swift-dev) | Native iOS and macOS apps in Swift 6 - SwiftUI, AppKit, SwiftData, concurrency, Swift Testing, XcodeGen, CallKit and audio, App Intents, devices, TestFlight, code signing, notarization. Use for any iPhone or Mac app, helper or CLI work. |
| `typescript-dev` | 0.5.0 | [page](https://clawhub.ai/tenequm/skills/typescript-dev) | Full-stack TypeScript with Vite 8, React 19, Tailwind v4, shadcn/ui, Biome, Vitest, and Hono 4. Use when setting up or working in a TypeScript project - components, styling, build and HMR, tests, lint/CI, or a Hono API with type-safe RPC. |
| `update-skill` | 0.10.0 | [page](https://clawhub.ai/tenequm/skills/update-skill) | Thorough on-demand refresh of one skill in a skills repo - researches usage, upstream, and docs in parallel, gates twice for approval, bumps version, updates CHANGELOG, validates, commits, watches CI. Use to check a skill's freshness. |
<!-- GENERATED_SKILLS_TABLE_END -->

## Releases

Every push to `main` publishes the skills whose `metadata.version` changed since the last `skills-*` tag to ClawHub, then cuts a GitHub release with per-skill notes. A changed skill without a version bump fails the release. Preview a release with `just release-plan`.

## Contributing

Issues and pull requests are welcome. Before opening a PR:

- bump `metadata.version` in every skill you edit
- run `just check` (offline lint; regenerates the README table - stage it) and `just preflight` (ClawHub dry-run, needs `clawhub login`)

Run `just setup` once per clone for the git hooks (`just check-ci` on commit, `just preflight` on push) and the `/update-skill` command.

## License

[MIT](LICENSE). ClawHub distributes every published skill under MIT-0.
