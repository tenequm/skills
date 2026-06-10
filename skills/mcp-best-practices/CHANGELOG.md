# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.6.0] - 2026-06-10

### Added
- New section "Spec Draft Direction (post-2025-11-25, unreleased)" - the draft spec's stateless/sessionless overhaul: removal of the `initialize` handshake and `Mcp-Session-Id` (SEP-2575/2567, state via server-minted handles passed as tool args), `server/discover` RPC, Multi Round-Trip Requests replacing server-initiated `roots/list`/`sampling`/`elicitation` (SEP-2322), `subscriptions/listen` (SEP-2575), `CacheableResult`/`ttlMs`/`cacheScope` (SEP-2549), required `Mcp-Method`/`Mcp-Name` headers + `x-mcp-header` (SEP-2243), schema loosening to full JSON Schema 2020-12 / any-JSON structuredContent (SEP-2106). Formal feature-lifecycle deprecation of Roots/Sampling/Logging (SEP-2577) and the HTTP+SSE transport (SEP-2596); DCR deprecated in favor of Client ID Metadata Documents (PR #2858); `iss` validation / issuer-keyed credentials (SEP-2468/2352). Flagged as unreleased draft; the TS SDK has begun landing 2026-07-28 wire-contract types on `main` (#2252).
- `transport-patterns.md`: operational gotchas for stateless servers - the client's SSE-opening `GET /mcp` is rejected with 406 (can tear down some clients); only `JSON.parse` the POST body and route GET/DELETE straight to the transport.

### Changed
- Quick Reference "Next" column for Spec now points to the draft direction instead of "-".
- ext-apps pin 1.7.2 -> 1.7.4 (1.7.3 lazy-auth-server example; 1.7.4 npm-audit/transitive security bumps - "No SDK API changes in this release"). SDK v1.29.0 and server 2.0.0-alpha.2 re-confirmed as the latest published versions.

Verified against: @modelcontextprotocol/ext-apps@1.7.4

## [0.5.0] - 2026-06-05

### Added
- New section "Tool Result Delivery: `content` vs `structuredContent`" - the dual-channel shadowing footgun, prominent in SKILL.md. Empirically tested Claude Code 2.1.165 delivery matrix (via `claude -p --output-format=stream-json`): when both a text block and `structuredContent` are returned, the text block is silently dropped and `structuredContent` wins; `outputSchema` makes zero difference; `content: []` + `structuredContent` works (stringified into the content slot). Includes the maintainer confirmation (anthropics/claude-code#9962, intentional since Claude Code v2.0.21), the spec's no-precedence-rule gap (Discussion #1563, SEP-1624 -> SEP-2200), and a cross-client table (Claude Code/Codex CLI/VS Code Copilot/Goose shadow; Cursor/Claude.ai web/ChatGPT prefer content or both; Google ADK forwards both).
- Server-author DO/DON'T rule: never return divergent `content`/`structuredContent`; if emitting `structuredContent`, mirror identical bytes into a text block (the spec's backwards-compat SHOULD); prefer one channel per tool/mode; `outputSchema` does not change delivery.

### Changed
- `structuredContent` is not a separate typed channel to the model on Claude Code - it is stringified into the `tool_result` content slot at the same token cost as JSON-as-text. Corrected the Token Bloat Mitigation bullet and the reference's "Token Benefits" -> "Token Reality" to stop implying a free out-of-band channel.
- v2 `registerTool` example and the `tool-schema-guide.md` weather example now carry inline comments that both channels MUST hold identical bytes.

## [0.4.0] - 2026-05-21

### Added
- Advisory-deprecation note for Roots, Sampling, and Logging (SEP-2577, final 2026-05-15) - no wire changes, features stay functional for 1+ year.
- Schema rule: `outputSchema` / nested response objects that forward upstream API data should default to `.passthrough()`; keep `inputSchema` strict.

### Changed
- ext-apps pin 1.7.1 -> 1.7.2 (example/dependency maintenance; no App-class API changes).
- #1643 (`z.union()`/`z.discriminatedUnion()` empty schema): clarified the fix landed in the v2 line (PR #1796); the v1.x backport (PR #2017) is still open, so the bug is present on every released v1 version.
- Resource-not-found error code: spec standardized on `-32602` (SEP-2164, final 2026-05-18); `-32002` is the legacy code clients should still accept. Corrects the earlier "new -32002" wording.
- v2 stable timeline: removed the unreliable "Q3 2026" / contradictory "Q1 2026" dates; only `2.0.0-alpha.2` is published.
- Tasks: SEP-1686 superseded by SEP-2663 (final, 2026-05-15) - Tasks moved out of the core `2025-11-25` spec into an official extension (`tasks/get` / `tasks/update` / `tasks/cancel`).

Verified against: @modelcontextprotocol/sdk@1.29.0, @modelcontextprotocol/server@2.0.0-alpha.2, @modelcontextprotocol/ext-apps@1.7.2

## [0.3.1] - 2026-04-30

### Changed
- Display-name alignment (Wave 2 repo-wide pass); no content changes.

## [0.3.0] - 2026-04-29

### Added
- AJV strict-validation gotcha for `outputSchema` / `structuredContent` (server Zod strips, client AJV rejects unstripped extras), with operational note about cached schemas.
- Path-aware `WWW-Authenticate.resource_metadata` discovery requirement (RFC 9728 / RFC 8414 path-insertion).
- v2 alpha breaking changes: unknown-tool returns JSON-RPC `-32602`; resource-not-found uses new `-32002`; `WebSocketClientTransport` removed; `discoverOAuthServerInfo()` and `AuthProvider` interface in v2 client.
- `@modelcontextprotocol/fastify` middleware adapter to v2 package list.
- ext-apps v1.7.0 surface: `App.registerTool()` / `sendToolListChanged()` (WebMCP-style), `createSamplingMessage`, `allowUnsafeEval` for strict CSP.
- ext-apps SEP-1865 stable status (2026-01-26).
- IETF `-32042` "Payment Required" code (`draft-payment-transport-mcp-00`) as canonical payment-error pattern alongside the ecosystem `isError` convention.
- CVE-2026-0621 (UriTemplate ReDoS) and CVE-2026-25536 (cross-client response leak); minimum SDK `≥ v1.26.0` requirement.
- Stdio-config command-injection warning (OX Security 2026-04-15 disclosure).
- Token-audience pitfalls (collapsed audience, opaque-vs-JWT) commonly hit when wiring Better-Auth / Auth0 to MCP.

### Changed
- TS SDK v1 stable pin: 1.28.0 → 1.29.0.
- v2 status: "pre-alpha on `main`" → "alpha published as `2.0.0-alpha.2`".
- v2 schema rules: any Standard Schema library works (Zod v4, Valibot, ArkType); `zod` dropped from `peerDependencies`; `fromJsonSchema` adapter for raw JSON Schema.
- ext-apps `App` class API names corrected: `app.log` → `sendLog`, `openUrl` → `openLink`, `updateContext` → `updateModelContext`; expanded method list.
- ext-apps `registerAppResource` signature corrected to `(server, name, uri, config, readCallback)`.
- MCP Registry status: "preview, breaking changes possible" → "preview, API freeze v0.1 since 2025-10-24".

### Fixed
- Known SDK Bugs table: #1643 (`z.discriminatedUnion()` empty schema) marked **Fixed on `main`** (closed 2026-03-30); flat-object workaround still useful for v1.x.
- Known SDK Bugs table: #1699 (transport closure stack overflow) marked **Fixed in PR #1788** (closed 2026-04-02).
- Known SDK Bugs table: #1619 (HTTP/2 + SSE Content-Length) marked **Closed** - reclassified as upstream `@hono/node-server#266`.
- Removed incorrect PR #1075 citation for `error.data` loss (that PR is a TS-Go check script); reframed as ecosystem-observed SDK behavior.

### Removed
- Stale "SDK v1 = Zod v3" rule and "Zod v4 Incompatibility (#925)" section - issue closed 2025-11-21; v1.23+ accepts Zod v3 or v4.

Verified against: @modelcontextprotocol/sdk@1.29.0, @modelcontextprotocol/server@2.0.0-alpha.2, @modelcontextprotocol/ext-apps@1.7.1

## [0.2.1] - 2026-04-09
- Initial CHANGELOG; tracking established.
