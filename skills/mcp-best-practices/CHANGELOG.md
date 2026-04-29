# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
