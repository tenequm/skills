# MCP Apps

Interactive HTML interfaces rendered inside MCP hosts. GA since January 2026 as the first official MCP extension (`io.modelcontextprotocol/ui`).

## Table of Contents
- [Architecture](#architecture)
- [Server Implementation](#server-implementation)
- [UI Implementation](#ui-implementation)
- [Project Setup](#project-setup)
- [CSP and Security](#csp-and-security)
- [Testing](#testing)
- [When to Use](#when-to-use)
- [Client Support](#client-support)

## Architecture

MCP Apps combine two MCP primitives: a **tool** that declares a UI resource in its metadata, and a **resource** that serves HTML rendered in a sandboxed iframe.

### Flow

1. **Tool registration**: Tool includes `_meta.ui.resourceUri` pointing to a `ui://` resource
2. **UI preloading**: Host can preload the resource before the tool is called (enables streaming inputs to the app)
3. **Resource fetch**: Host fetches the HTML from the server via `resources/read`
4. **Sandboxed rendering**: Host renders HTML in a sandboxed iframe (no parent DOM/cookie/storage access)
5. **Bidirectional communication**: App and host communicate via postMessage using a JSON-RPC dialect of MCP

```
Agent ──tools/call──────> MCP Server
Agent <──result────────── MCP Server
Agent ──result pushed────> MCP App (iframe)
User  ──interaction──────> MCP App (iframe)
App   ──tools/call───────> Agent ──> MCP Server
Agent <──result────────── MCP Server
Agent ──result───────────> MCP App (iframe)
App   ──context update───> Agent (updates model context)
```

### Key Packages

| Package | Purpose |
|---------|---------|
| `@modelcontextprotocol/ext-apps` | Server helpers (`registerAppTool`, `registerAppResource`) + client `App` class |
| `@mcp-ui/client` | React components for hosts rendering MCP Apps ([docs](https://mcpui.dev/)) |

## Server Implementation

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import {
  registerAppTool,
  registerAppResource,
  RESOURCE_MIME_TYPE,
} from "@modelcontextprotocol/ext-apps/server";
import fs from "node:fs/promises";
import path from "node:path";

const server = new McpServer({ name: "My App Server", version: "1.0.0" });

// ui:// scheme tells hosts this is an MCP App resource
const resourceUri = "ui://my-tool/mcp-app.html";

// Register tool with UI metadata
registerAppTool(server, "my-tool", {
  title: "My Tool",
  description: "Does something and shows an interactive UI",
  inputSchema: { query: z.string().describe("Search query") },
  _meta: { ui: { resourceUri } },
}, async ({ query }) => {
  const result = await doWork(query);
  return { content: [{ type: "text", text: JSON.stringify(result) }] };
});

// Register resource serving bundled HTML
registerAppResource(server, resourceUri, resourceUri, {
  mimeType: RESOURCE_MIME_TYPE,
}, async () => {
  const html = await fs.readFile(
    path.join(import.meta.dirname, "dist", "mcp-app.html"), "utf-8"
  );
  return { contents: [{ uri: resourceUri, mimeType: RESOURCE_MIME_TYPE, text: html }] };
});
```

**Key points**:
- `registerAppTool` sets `_meta.ui.resourceUri` on the tool definition
- `registerAppResource` serves the HTML when the host requests the UI resource
- `RESOURCE_MIME_TYPE` = `text/html;profile=mcp-app`
- The `ui://` path structure is arbitrary - organize however makes sense

### Express Server Boilerplate

```typescript
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import cors from "cors";
import express from "express";

const app = express();
app.use(cors());
app.use(express.json());

app.post("/mcp", async (req, res) => {
  const transport = new StreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });
  res.on("close", () => transport.close());
  await server.connect(transport);
  await transport.handleRequest(req, res, req.body);
});

app.listen(3001);
```

## UI Implementation

```html
<!-- mcp-app.html -->
<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8" /><title>My App</title></head>
<body>
  <div id="app">Loading...</div>
  <button id="refresh">Refresh</button>
  <script type="module" src="/src/mcp-app.ts"></script>
</body>
</html>
```

```typescript
// src/mcp-app.ts
import { App } from "@modelcontextprotocol/ext-apps";

const app = new App({ name: "My App", version: "1.0.0" });

// Establish communication with host (call once on init)
app.connect();

// Handle initial tool result pushed by host
app.ontoolresult = (result) => {
  const text = result.content?.find((c) => c.type === "text")?.text;
  document.getElementById("app")!.textContent = text ?? "[ERROR]";
};

// Proactively call tools from UI interactions
document.getElementById("refresh")!.addEventListener("click", async () => {
  const result = await app.callServerTool({
    name: "my-tool",
    arguments: { query: "updated" },
  });
  const text = result.content?.find((c) => c.type === "text")?.text;
  document.getElementById("app")!.textContent = text ?? "[ERROR]";
});
```

### App Class API

| Method | Purpose |
|--------|---------|
| `app.connect()` | Establish postMessage communication with host (call once on init) |
| `app.ontoolresult` | Callback when host pushes a tool result to the app |
| `app.callServerTool({ name, arguments })` | Call any tool on the MCP server (round-trip, handle latency) |
| `app.log(level, message)` | Send log messages to host |
| `app.openUrl(url)` | Request host to open a URL |
| `app.updateContext(data)` | Update model context with structured data from the app |

The `App` class is a convenience wrapper, not a requirement. You can implement the [postMessage protocol](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx) directly.

## Project Setup

### Directory Structure

```
my-mcp-app/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── server.ts          # MCP server with tool + resource
├── mcp-app.html       # UI entry point
└── src/
    └── mcp-app.ts     # UI logic
```

### Dependencies

```bash
npm install @modelcontextprotocol/ext-apps @modelcontextprotocol/sdk
npm install -D typescript vite vite-plugin-singlefile express cors @types/express @types/cors tsx
```

### Configuration

```json
// package.json
{
  "type": "module",
  "scripts": {
    "build": "INPUT=mcp-app.html vite build",
    "serve": "npx tsx server.ts"
  }
}
```

```typescript
// vite.config.ts
import { defineConfig } from "vite";
import { viteSingleFile } from "vite-plugin-singlefile";

export default defineConfig({
  plugins: [viteSingleFile()],
  build: {
    outDir: "dist",
    rollupOptions: { input: process.env.INPUT },
  },
});
```

`vite-plugin-singlefile` bundles all CSS/JS into a single HTML file, avoiding CSP issues. Optional - you can serve unbundled files if you [configure CSP](https://apps.extensions.modelcontextprotocol.io/api/documents/Patterns.html#configuring-csp-and-cors).

### Build and Run

```bash
npm run build && npm run serve
```

## CSP and Security

MCP Apps render in sandboxed iframes with **deny-by-default CSP**. The sandbox prevents:
- Accessing parent window DOM
- Reading host cookies or localStorage
- Navigating the parent page
- Executing scripts in parent context

All communication goes through postMessage. The host controls which capabilities the app can access.

**External resources** (CDN scripts, fonts, APIs): Configure via `_meta.ui.csp` in tool registration, or bundle everything into a single HTML file.

**Additional capabilities** (microphone, camera): Request via `_meta.ui.permissions` in tool registration.

## Testing

### With basic-host (local development)

```bash
git clone https://github.com/modelcontextprotocol/ext-apps.git
cd ext-apps/examples/basic-host && npm install
SERVERS='["http://localhost:3001/mcp"]' npm start
# Navigate to http://localhost:8080
```

### With Claude (via cloudflared tunnel)

```bash
# Terminal 1: Run your server
npm run build && npm run serve

# Terminal 2: Expose to internet
npx cloudflared tunnel --url http://localhost:3001
```

Copy the generated URL and add as a custom connector in Claude: Profile > Settings > Connectors > Add custom connector. Requires paid Claude plan (Pro, Max, or Team).

## When to Use

MCP Apps fit when your use case involves:
- **Complex data exploration** - interactive charts, maps, drill-down views
- **Multi-option configuration** - forms with validation, defaults, interdependencies
- **Rich media** - PDF viewers, 3D models, image previews, video players
- **Real-time monitoring** - live dashboards, logs, system status
- **Multi-step workflows** - approval flows, triage, code review

If you don't need conversation-integrated UI, a regular web app is simpler.

## Client Support

| Client | MCP Apps |
|--------|----------|
| Claude (web + Desktop) | Yes |
| ChatGPT | Yes |
| VS Code Copilot | Yes |
| Goose | Yes |
| Postman | Yes |
| MCPJam | Yes |

### Framework Templates

The [ext-apps repo](https://github.com/modelcontextprotocol/ext-apps/tree/main/examples) includes starters for React, Vue, Svelte, Preact, Solid, and vanilla JS.

### Building a Host

Two approaches for rendering MCP Apps in your own client:
1. **`@mcp-ui/client`** - React components ([docs](https://mcpui.dev/))
2. **App Bridge** - SDK module for iframe rendering, message passing, tool proxying, security ([docs](https://apps.extensions.modelcontextprotocol.io/api/modules/app-bridge.html))

Full API documentation: [apps.extensions.modelcontextprotocol.io](https://apps.extensions.modelcontextprotocol.io/api/)
