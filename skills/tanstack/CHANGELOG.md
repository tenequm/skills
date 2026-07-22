# Changelog

All notable changes to this skill will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/2.0.0/),
and this skill adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.2] - 2026-07-22

### Added

- skill-card.md release record following NVIDIA's skill-card format
- metadata.openclaw block (emoji, homepage) for ClawHub display

## [0.4.1] - 2026-07-10

### Changed
- CHANGELOG preamble pinned to Keep a Changelog 2.0.0 (format unchanged; KaC 2.0.0 keeps existing changelogs valid).

## [0.4.0] - 2026-07-01

### Fixed
- infinite-queries.md: removed the v4-only `refetchPage` invalidation API (deleted
  in Query v5) from three examples; replaced with the `maxPages` option, which caps
  stored and refetched pages (TanStack Query migrating-to-v5: "Removed `refetchPage`
  in favor of `maxPages`").

### Added
- Query: `useIsFetching` / `useIsMutating` for app-wide loading/mutating indicators
  (query-guide.md).
- Query: `maxPages` option to cap stored/refetched pages in infinite queries
  (infinite-queries.md).
- Query: `usePrefetchQuery` / `usePrefetchInfiniteQuery` render-phase prefetch hooks,
  distinct from the imperative `queryClient.prefetchQuery` (query-performance.md).
- Query: referential-stability footgun - `data ?? []` and per-render new objects/proxy
  getters in queryKeys or effect deps cause infinite refetch loops / "Maximum update
  depth exceeded"; use hoisted stable constants (query-guide.md).
- Router: View Transitions - `viewTransition` on Link/navigate, `defaultViewTransition`
  on the router (routing-patterns.md).
- Router: route lifecycle callbacks `onEnter` / `onStay` / `onLeave` and `remountDeps`
  remount control (routing-patterns.md).
- Router: `createLink` / `useLinkProps` for custom, type-safe Link components wrapping
  UI-library anchors (router-guide.md).
- Start: testing a server function via curl requires the `x-tsr-serverFn: true` header,
  else the handler never runs; thrown errors return HTTP 200 with the error framed in
  the body (server-functions.md).

Verified against: @tanstack/react-query@5.101.2, @tanstack/react-router@1.170.16, @tanstack/react-start@1.168.26

## [0.3.0] - 2026-06-10

### Changed
- Server functions & middleware: renamed `.inputValidator()` -> `.validator()`
  across SKILL.md, server-functions.md, middleware.md, start-guide.md (29 call
  sites). `validator()` is now the canonical method; `inputValidator()` is
  deprecated and the compiler emits warnings for it (TanStack/router PR #7566).
- start-guide.md: dropped the stale "Release Candidate" header and the "No RSC
  support yet" claim, aligning it with SKILL.md (Pre-1.0; RSC experimental opt-in).

### Added
- Query cross-reload persistence setup (query-performance.md):
  `PersistQueryClientProvider` + storage persister, `gcTime >= maxAge`, `buster`
  for cache-shape changes, and excluding credential-bearing queries via
  `shouldDehydrateQuery`; corrected the React package name to
  `@tanstack/react-query-persist-client`.
- Network Mode note (`online` / `always` / `offlineFirst`) in query-performance.md.
- `useMutationState` note for shared cross-component mutation UI in query-guide.md.

Verified against: @tanstack/react-router@1.170.15, @tanstack/react-start@1.168.25, @tanstack/router-plugin@1.168.18

## [0.2.0] - 2026-06-04

### Changed
- Start: dropped the "(RC)" label and the "No RSC yet" claim. The docs overview no
  longer uses RC; React Server Components are now an experimental feature (opt-in via
  `tanstackStart({ rsc: { enabled: true } })` + `@vitejs/plugin-rsc`, React 19 / Vite 7+).
- Start scaffolding command updated from `pnpm create @tanstack/start@latest` to
  `npx @tanstack/cli@latest create` (or TanStack Builder).
- Deployment: Cloudflare, Netlify, and Railway are now the official hosting partners.
- Sharpened the auth best practice: the security boundary is the server function /
  server route / endpoint that touches private data, not `beforeLoad` route guards
  (SKILL.md best practice, middleware.md, server-functions.md).

### Added
- Zod v4 note: the zod-adapter is no longer needed with Zod v4 (pass the schema
  directly to `validateSearch`; `.catch()` retains types).
- CSRF default-middleware caveat: defining `src/start.ts` requires re-adding
  `createCsrfMiddleware()` explicitly for server functions.
- `createServerFn({ strict })` serialization-check opt-out (server-functions.md, start-guide.md).
- Native `mutationOptions()` helper (companion to `queryOptions()`) in query-guide.md.
- Server-function Cache-Control safety: `public` only for non-identity data; authed
  responses need `private` + `Vary` or `no-store` (server-functions.md).
- Real-world footguns: invalidate-then-navigate stale data, queryKey runtime
  dimensions, StrictMode double-submit, `staleTime` is not cross-reload persistence
  (Query); dot-prefixed dirs excluded from the route tree, `Link to` rejects dynamic
  strings, client-only-provider hydration mismatches (Router/Start).

### Fixed
- Stale Start doc URLs updated to include the `/guide/` path segment.

- Initial CHANGELOG; upstream tracking established.

Verified against: @tanstack/react-query@5.101.0, @tanstack/react-router@1.170.11, @tanstack/react-start@1.168.19, @tanstack/zod-adapter@1.167.0, @tanstack/router-plugin@1.168.14
