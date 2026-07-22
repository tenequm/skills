# Skill Card

## Description

tanstack guides building type-safe React applications with TanStack Query (server-state fetching, caching, mutations), TanStack Router (file-based routing, validated search params, loaders), and TanStack Start (SSR, server functions, middleware). It provides working setup, patterns, and deep-dive references for all three libraries.

This skill is ready for commercial and non-commercial use.

## Owner

opwizardx (tenequm/skills, https://github.com/tenequm/skills)

## License/Terms of Use

MIT-0 when installed from ClawHub (registry-wide license for all published skills). Source repository https://github.com/tenequm/skills is licensed Apache-2.0; a LICENSE.txt copy ships in this bundle.

## Use Case

React/TypeScript developers building SPAs or full-stack apps on the TanStack libraries: wiring QueryClient and query/mutation patterns, setting up file-based routing with typed navigation and search params, or adding SSR and server functions with Start. The agent uses it to write correct v5/v1 API code and load per-topic references (infinite queries, code splitting, middleware, deployment).

## Deployment Geography for Use

Global

### Requirements / Dependencies

Requires API Key or External Credential: No
Credential Type(s): None

Do not include secrets in prompts, logs, or output; use least-privilege credentials; rotate keys as appropriate.

Packages the skill instructs the agent to install: @tanstack/react-query, @tanstack/react-router, @tanstack/router-plugin, @tanstack/react-start, @tanstack/zod-adapter, @tanstack/react-query-devtools, zod; installed via npm/pnpm alongside Vite and React.

## Known Risks and Mitigations

Risk: Generated code has security-relevant patterns that are easy to get wrong: loaders are isomorphic (secrets placed in them leak to the client), and creating src/start.ts silently disables Start's auto-installed CSRF middleware unless re-added.

Mitigation: The skill states both rules explicitly (secrets only in createServerFn, re-add createCsrfMiddleware, authorize at the data boundary); users should review server/client boundaries and middleware config before deploying.

Risk: API guidance drifts from fast-moving upstreams - Start is pre-1.0, RSC support is experimental, and Zod v3 vs v4 changes the search-param validation pattern.

Mitigation: metadata.upstream pins the verified library versions and the CHANGELOG records verification dates; check installed package versions against the pinned ones and consult official docs when they diverge.

Risk: Setup snippets modify build configuration (vite.config.ts plugin order matters: viteReact must come after tanstackStart) and generate route files, which can break an existing app if applied blindly.

Mitigation: Apply configuration changes on a branch and run the dev server and type checks after each change; the skill documents the required plugin ordering.

## References

- TanStack Query docs: https://tanstack.com/query/latest/docs/framework/react/overview
- TanStack Router docs: https://tanstack.com/router/latest/docs/framework/react/overview
- TanStack Start docs: https://tanstack.com/start/latest/docs/framework/react/overview
- Tracked upstream versions: @tanstack/react-query@5.101.2, @tanstack/react-router@1.170.16, @tanstack/react-start@1.168.26, @tanstack/zod-adapter@1.167.0, @tanstack/router-plugin@1.168.18
- Source: https://github.com/tenequm/skills/tree/main/skills/tanstack

## Skill Output

Output type(s): React/TypeScript application code (queries, mutations, routes, server functions, middleware), build configuration, and install commands.

Output format: TypeScript/TSX code blocks in Markdown; files written into the user's project when requested.

Output parameters: Follows TanStack conventions (queryOptions factories, hierarchical query keys, src/routes/ file-based routing, routeTree.gen).

Other properties: Install commands fetch packages from npm; generated server functions and loaders execute in the user's app, not in the skill.

## Skill Version

0.4.2

## Ethical Considerations

Server functions and loaders generated from this skill sit on the app's security boundary; humans should review auth, CSRF, and secret handling before shipping. The skill's guidance reflects specific pinned library versions and is not a substitute for the official docs on breaking changes.
