# Extensions and Registry

MCP extensions system, authorization extensions, and the MCP Registry.

## Table of Contents
- [Extensions System](#extensions-system)
- [Authorization Extensions](#authorization-extensions)
- [MCP Registry](#mcp-registry)
- [Server Capabilities Beyond Tools](#server-capabilities-beyond-tools)

## Extensions System

Extensions are optional, strictly additive capabilities layered on the core MCP protocol. They enable modular features (auth), specialized behavior (domain-specific), and experimental incubation without changing the core spec.

### Three-Layer Architecture

1. **MCP Core Specification** - baseline client-server interoperability
2. **MCP Projects** - supporting infrastructure (Registry, Inspector)
3. **MCP Extensions** - optional patterns for specialized use cases

### Extension Identifiers

Format: `{vendor-prefix}/{extension-name}`

| Prefix | Usage |
|--------|-------|
| `io.modelcontextprotocol` | Official extensions |
| Reversed domain (e.g., `com.example`) | Third-party extensions |

### Official Extensions

| Extension | Identifier | Status | Repo |
|-----------|-----------|--------|------|
| MCP Apps | `io.modelcontextprotocol/ui` | Stable (SEP-1865, 2026-01-26); SDK `ext-apps@2.0.0` 2026-09-08 | [ext-apps](https://github.com/modelcontextprotocol/ext-apps) |
| OAuth Client Credentials | `io.modelcontextprotocol/oauth-client-credentials` | Draft | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |
| Enterprise-Managed Auth | `io.modelcontextprotocol/enterprise-managed-authorization` | Stable (2026-06-18) | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |
| Tasks | `io.modelcontextprotocol/tasks` | Official (SEP-2663, final 2026-05-15); repo dropped its "experimental" framing 2026-08-19, schema frozen Stable at `2026-07-28` | [ext-tasks](https://github.com/modelcontextprotocol/ext-tasks) |

### Negotiation

**2025-era wires** - both sides declare extension support in `extensions` during initialization:

```json
// Client (initialize request)
{
  "capabilities": {
    "extensions": {
      "io.modelcontextprotocol/ui": { "mimeTypes": ["text/html;profile=mcp-app"] }
    }
  }
}

// Server (initialize response)
{
  "capabilities": {
    "extensions": { "io.modelcontextprotocol/ui": {} }
  }
}
```

**On 2026-07-28** there is no `initialize`, so this exchange does not exist. Clients advertise extension support **per request**:

> Clients advertise extension support in `_meta["io.modelcontextprotocol/clientCapabilities"]` within each request

Servers advertise theirs in the `capabilities` of their `server/discover` result. The `extensions` field was added to both `ClientCapabilities` and `ServerCapabilities` in this revision.

Each extension defines its settings schema. Empty object = no settings.

**Graceful degradation**: If one side supports an extension but the other doesn't, fall back to core protocol behavior or reject with an error if mandatory. Always provide meaningful text content alongside UI-enhanced responses so non-supporting clients still work.

### Creating Extensions

Official extensions follow the SEP (Specification Enhancement Proposal) process ([SEP-2133](https://modelcontextprotocol.io/seps/2133-extensions)):

1. **Propose** - Create SEP with type "Extensions Track" per [SEP guidelines](https://modelcontextprotocol.io/community/sep-guidelines)
2. **Implement** - Build at least one reference implementation in an official SDK (required before review)
3. **Review** - Core Maintainers review and approve
4. **Publish** - Add to extension repository
5. **Adopt** - Other clients/servers implement

Requirements:
- RFC 2119 language (MUST, SHOULD, MAY)
- Associated working group or interest group
- Extensions always disabled by default - explicit opt-in required
- SDKs choose which extensions to support (not required for conformance)

### Experimental Extensions

Working Groups can incubate extensions in repos with `experimental-ext-` prefix within the MCP GitHub org. Requirements:
- Associated with a Working Group or Interest Group
- Clear experimental labeling in README and package name
- Core Maintainer oversight (can archive/remove)
- Graduate to official via standard SEP process

### Evolution

Extensions evolve independently of the core protocol. Prefer capability flags or versioning within the extension settings over new identifiers. New identifier only for breaking changes (e.g., `io.modelcontextprotocol/my-extension-v2`).

Breaking changes: removing/renaming fields, changing types, altering semantics, adding required fields.

### Client Support Matrix

| Client | MCP Apps | OAuth Client Creds | Enterprise Auth |
|--------|----------|-------------------|-----------------|
| Claude (web + Desktop) | Yes | - | - |
| ChatGPT | Yes | - | - |
| VS Code Copilot | Yes | - | - |
| Goose | Yes | - | - |
| Postman | Yes | - | - |
| MCPJam | Yes | - | - |
| Microsoft 365 Copilot | Yes | - | - |
| Cursor | Yes | - | - |
| Archestra.AI | Yes | - | Yes |
| PostHog Code | Yes | - | - |

Enterprise-Managed Authorization reached **Stable** (2026-06-18); Archestra.AI is the first client shipping it. OAuth Client Credentials remains Draft with no client adoption yet - check the official [client matrix](https://modelcontextprotocol.io/extensions/client-matrix) and [ext-auth](https://github.com/modelcontextprotocol/ext-auth) for latest status.

## Authorization Extensions

The core MCP spec includes OAuth 2.1 authorization (authorization code + PKCE) for interactive user consent. Auth extensions address scenarios where this doesn't fit.

Source: [ext-auth repo](https://github.com/modelcontextprotocol/ext-auth)

### OAuth Client Credentials

**Identifier**: `io.modelcontextprotocol/oauth-client-credentials`

Machine-to-machine authentication via OAuth 2.1 client credentials flow. No user interaction required.

**Use cases**: Background services/daemons, CI/CD pipelines, server-to-server API integrations.

### Enterprise-Managed Authorization

**Identifier**: `io.modelcontextprotocol/enterprise-managed-authorization`

Centralized access control via enterprise identity providers (IdPs). Employees access MCP servers through their organization's existing IdP without per-server authorization.

**Use cases**: Enterprise employees at work, organization-wide MCP access policy enforcement.

### Decision Table

| Scenario | Auth Approach |
|----------|--------------|
| Background service / daemon | OAuth Client Credentials |
| CI/CD pipeline | OAuth Client Credentials |
| Server-to-server integration | OAuth Client Credentials |
| Enterprise employees at work | Enterprise-Managed Authorization |
| Org-wide policy enforcement | Enterprise-Managed Authorization |
| Standard interactive user auth | Core MCP spec (no extension needed) |

Both use standard extension negotiation. Specified in [ext-auth/specification/draft](https://github.com/modelcontextprotocol/ext-auth/tree/main/specification/draft).

## MCP Registry

The official centralized metadata repository for publicly accessible MCP servers. Currently in **preview**, but the API entered a **v0.1 freeze on 2025-10-24** with a stability commitment for integrators (no breaking changes during the freeze window). Backed by Anthropic, GitHub, PulseMCP, and Microsoft.

### What It Provides

- Single place for server creators to publish metadata
- Namespace management via DNS verification
- REST API for clients and aggregators to discover servers
- Standardized `server.json` format with name, location, execution instructions, capabilities

### Key Concepts

**Not a package registry**: Hosts metadata that *points to* packages on npm, PyPI, Docker Hub, etc. Doesn't host code.

**Namespace authentication**: Server names use reverse DNS format (`io.github.user/server-name`, `com.example/server`). Only verified owners (via GitHub account or DNS/HTTP challenge) can publish under their namespace.

**Package types**: beyond npm, PyPI and Docker/OCI, the registry now accepts **Cargo** (crates.io only - *"For Cargo packages, the MCP Registry currently supports the official crates.io registry (`https://crates.io`) only"*), **NuGet**, and **MCPB** - *"prebuilt binary distributed via GitHub or GitLab Releases. End users need no toolchain."*

**Ownership is proven from inside the package**, via an `mcp-name:` token in the published README. One gotcha bites Rust publishers specifically: *"Unlike PyPI and NuGet (which preserve HTML comments in their README rendering), **crates.io strips HTML comments during markdown -> HTML conversion**"* - so on crates.io the token has to be visible text, not a hidden comment.

**Public servers only**: Private servers (internal networks, private registries) are not supported. Self-host for those.

**Aggregator-first design**: Intended for consumption by downstream aggregators (marketplaces, catalogs) via REST API, not direct use by host applications. Aggregators poll periodically (e.g., hourly).

**OpenAPI spec**: Other registries can implement the same [OpenAPI spec](https://github.com/modelcontextprotocol/registry/blob/main/docs/reference/api/openapi.yaml) for standardized host application support.

### Publishing

Quickstart: [modelcontextprotocol.io/registry/quickstart](https://modelcontextprotocol.io/registry/quickstart)

Automate with GitHub Actions: [modelcontextprotocol.io/registry/github-actions](https://modelcontextprotocol.io/registry/github-actions)

Server metadata is `server.json` containing: unique name, location (npm package, remote URL), execution instructions (args, env vars), description, capabilities.

### Trust and Security

- **Namespace verification** prevents impersonation
- **Security scanning** delegated to underlying package registries (npm, PyPI, Docker Hub) and downstream aggregators
- **Spam prevention**: namespace auth requirements, character limits/validation, manual takedown by maintainers

### Versioning

Servers are versioned within the registry. See [versioning guide](https://modelcontextprotocol.io/registry/versioning) for release management.

## Server Capabilities Beyond Tools

The spec includes server-to-client request capabilities. Elicitation and Progress are core protocol features; Sampling is Deprecated (SEP-2577) and Tasks has moved to an official extension (SEP-2663).

> **Shape change on 2026-07-28.** Servers can no longer send requests to clients at all. Elicitation and sampling are reached through **Multi Round-Trip Requests**: the tool returns an `InputRequiredResult` carrying `inputRequests`, and the client answers with `inputResponses` on a retry of the original request. The `ctx.mcpReq.*` call style below is the 2025-era API - still what the SDK does by default. See `references/spec-2026-07-28.md`.

### Elicitation

Request structured user input mid-tool-execution. Server sends a schema, client prompts the user, returns the response.

```typescript
// v2 API
const input = await ctx.mcpReq.elicitInput({
  message: "Please confirm the operation",
  requestedSchema: {
    type: "object",
    properties: { confirm: { type: "boolean" } },
  },
});
```

Related SEPs: [#1034](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1034) (default values), [#1036](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1036) (URL mode for out-of-band interactions), [#1330](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1330) (enum improvements).

### Sampling

> **Advisory-deprecated.** [SEP-2577](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2577) (final, 2026-05-15) deprecates Sampling along with Roots and Logging. No wire-level changes - the feature stays functional for 1+ year - but adoption is low and it is complex to implement (human-in-the-loop, model selection, security). Do not build new servers that depend on it.

Request an LLM completion from the client. Enables agentic patterns where tools delegate reasoning to the model.

```typescript
// v2 API
const response = await ctx.mcpReq.requestSampling({
  messages: [{ role: "user", content: { type: "text", text: "Summarize this data" } }],
  maxTokens: 100,
});
```

**Sampling with tools is released, not proposed.** SEP-1577 landed in the 2026-07-28 schema: `CreateMessageRequest` carries `tools?: Tool[]` and `toolChoice?: ToolChoice`, with `ToolUseContent`/`ToolResultContent` for the exchange. It is gated on a sub-capability - *"The client MUST return an error if this field is provided but `ClientCapabilities.sampling.tools` is not declared. Default is `{ mode: \"auto\" }`."*

**Capabilities have sub-flags now.** Both sampling and elicitation are structured rather than boolean, so "the client supports elicitation" is not a single fact to check:

```typescript
elicitation?: { form?: JSONObject; url?: JSONObject; };
sampling?:    { context?: JSONObject; tools?: JSONObject; };
```

Check the specific sub-flag you need (`elicitation.url` for out-of-band flows, `sampling.tools` for tool-augmented sampling) before relying on it.

### Tasks (SEP-2663)

Long-running operations with lifecycle management - progress tracking, cancellation, and status updates for operations spanning multiple requests. [SEP-2663](https://github.com/modelcontextprotocol/modelcontextprotocol/pull/2663) (final, 2026-05-15) supersedes the earlier SEP-1686 proposal: Tasks moved out of the core `2025-11-25` spec (the experimental `tasks` feature there is removed) into the official `io.modelcontextprotocol/tasks` extension. A server may answer a `tools/call` with an async task handle instead of a final result; the client **polls** via `tasks/get` and `tasks/update` (`tasks/cancel` to abort). The redesign drops the blocking `tasks/result` and `tasks/list` methods and allows servers to return task handles unsolicited.

**Canonical source**: the [ext-tasks repo](https://github.com/modelcontextprotocol/ext-tasks) holds the full specification, with docs at [/docs/extensions/tasks/overview](https://modelcontextprotocol.io/docs/extensions/tasks/overview). The stale "experimental" README banner was removed on 2026-08-19; the repo now opens *"This repository contains the official Model Context Protocol Tasks extension"* and pins an immutable `2026-07-28` Stable schema snapshot.

**Three rules that changed or are easy to miss:**

- **Missing-capability code is now `-32021`, renumbered from `-32003`.** *"If a server is unable to service a request to a client that does not declare this extension capability without returning `CreateTaskResult`, the server **MUST** return an error with the code `-32021` (Missing Required Client Capability), indicating the required extension."* Tasks is per-request opt-in: to a client that did not declare it, answer synchronously or return `-32021` - never a task handle it cannot poll.
- **Authorize every task request, not just task creation.** *"Servers **MUST** perform authentication and authorization checks on each task-related request to ensure that the client has permission to access a task."* And because a task ID may function as a bearer token for stored state, servers **MUST** generate them *"with sufficient entropy that a third party cannot enumerate or guess them"* - the same discipline as the stateful-tool handles in `SKILL.md`.
- **`CreateTaskResult` must not outrun durability.** A server **MUST NOT** return it *"until the task is durably created - that is, until a `tasks/get` for the returned `taskId` would resolve"*, waiting for consistency in eventually-consistent stores. That removes the need for clients to speculatively poll.

In TypeScript SDK v2 the entire 2025-era task wire vocabulary is `@deprecated` - importable for backwards compatibility, but excluded from the typed method maps (`RequestMethod`, `RequestTypeMap`, `ResultTypeMap`, `NotificationTypeMap` carry no `tasks/*` entries), and removable at the major version that drops 2025-era support.

### Progress

Report incremental progress on any request:

```typescript
// v2 API
await ctx.mcpReq.sendProgress({ progress: 50, total: 100 });
```
