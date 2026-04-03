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

| Extension | Identifier | Repo |
|-----------|-----------|------|
| MCP Apps | `io.modelcontextprotocol/ui` | [ext-apps](https://github.com/modelcontextprotocol/ext-apps) |
| OAuth Client Credentials | `io.modelcontextprotocol/oauth-client-credentials` | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |
| Enterprise-Managed Auth | `io.modelcontextprotocol/enterprise-managed-authorization` | [ext-auth](https://github.com/modelcontextprotocol/ext-auth) |

### Negotiation

Both sides declare extension support in `extensions` during initialization:

```json
// Client (initialize request)
{
  "capabilities": {
    "extensions": {
      "io.modelcontextprotocol/ui": {
        "mimeTypes": ["text/html;profile=mcp-app"]
      }
    }
  }
}

// Server (initialize response)
{
  "capabilities": {
    "extensions": {
      "io.modelcontextprotocol/ui": {}
    }
  }
}
```

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

Auth extensions not yet widely adopted. Check [ext-auth](https://github.com/modelcontextprotocol/ext-auth) for latest status.

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

The official centralized metadata repository for publicly accessible MCP servers. Currently in **preview** (breaking changes possible). Backed by Anthropic, GitHub, PulseMCP, and Microsoft.

### What It Provides

- Single place for server creators to publish metadata
- Namespace management via DNS verification
- REST API for clients and aggregators to discover servers
- Standardized `server.json` format with name, location, execution instructions, capabilities

### Key Concepts

**Not a package registry**: Hosts metadata that *points to* packages on npm, PyPI, Docker Hub, etc. Doesn't host code.

**Namespace authentication**: Server names use reverse DNS format (`io.github.user/server-name`, `com.example/server`). Only verified owners (via GitHub account or DNS/HTTP challenge) can publish under their namespace.

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

The spec includes server-to-client request capabilities. These aren't extensions - they're core protocol features that extend what tools can do.

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

Request an LLM completion from the client. Enables agentic patterns where tools delegate reasoning to the model.

```typescript
// v2 API
const response = await ctx.mcpReq.requestSampling({
  messages: [{ role: "user", content: { type: "text", text: "Summarize this data" } }],
  maxTokens: 100,
});
```

Related SEP: [#1577](https://github.com/modelcontextprotocol/modelcontextprotocol/issues/1577) (Sampling With Tools - allow sampling requests to include tool definitions).

### Tasks (SEP-1686)

Long-running operations with lifecycle management. Enables progress tracking, cancellation, and status updates for operations spanning multiple requests.

### Progress

Report incremental progress on any request:

```typescript
// v2 API
await ctx.mcpReq.sendProgress({ progress: 50, total: 100 });
```
