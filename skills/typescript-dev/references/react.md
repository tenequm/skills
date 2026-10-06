# React 19

Patterns for type-safe React 19.3 components (latest `19.3.0`). The headline shift from older React: **the React Compiler handles memoization**, `ref` is a normal prop, and `use()` reads context and promises without the old hook-placement rules. Write plain components and let the tooling optimize. For TypeScript specifics (props typing, generics, tsconfig) see [typescript.md](typescript.md).

## Critical rules

### `ref` is a prop - no `forwardRef`

```tsx
// React 19: ref is a regular prop
function Input({ ref, ...props }: React.ComponentProps<"input"> & { ref?: React.Ref<HTMLInputElement> }) {
  return <input ref={ref} {...props} />
}
```

`React.ComponentProps<"input">` already includes `ref` in React 19's types, so for plain DOM-wrapping components you usually just destructure `ref` from props without declaring it.

### No manual memoization

The compiler auto-memoizes return values, expensive computations, and callbacks. Drop `memo`, `useMemo`, `useCallback` from the common path:

```tsx
// Plain code - compiler memoizes sorting, the callback, and the JSX
function List({ items, onSelect }: { items: Item[]; onSelect: (id: string) => void }) {
  const sorted = items.toSorted(compare)
  return sorted.map((item) => <Row key={item.id} onClick={() => onSelect(item.id)} />)
}
```

### Extend native element props

```tsx
type ButtonProps = React.ComponentProps<"button"> & { variant?: "primary" | "ghost" }
```

### `use()` over `useContext()`

`use()` can read context after early returns and inside conditionals - `useContext` cannot. Pair it with a factory hook that throws on a missing provider so consumers never null-check:

```tsx
const AuthContext = createContext<AuthState | null>(null)

function useAuth(): AuthState {
  const ctx = use(AuthContext)
  if (ctx === null) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}
```

## React 19 patterns

### Component authoring

Plain functions with `data-slot` for styling hooks (the shadcn convention). No `forwardRef`, no `FC`:

```tsx
function Card({ className, ...props }: React.ComponentProps<"div">) {
  return <div data-slot="card" className={cn("rounded-xl border bg-card", className)} {...props} />
}
```

### Actions

Async transitions handle pending state, errors, and form resets. `useActionState` for forms:

```tsx
function UpdateProfile({ userId }: { userId: string }) {
  const [error, submitAction, isPending] = useActionState(
    async (_prev: string | null, formData: FormData) => {
      const result = await updateProfile(userId, formData)
      return result.error ?? null
    },
    null
  )
  return (
    <form action={submitAction}>
      <input name="displayName" required />
      <button type="submit" disabled={isPending}>{isPending ? "Saving..." : "Save"}</button>
      {error && <p className="text-destructive">{error}</p>}
    </form>
  )
}
```

`useTransition` for non-form Actions; `useOptimistic` for instant feedback:

```tsx
const [isPending, startTransition] = useTransition()
// onClick={() => startTransition(async () => { await onDelete() })}

const [optimisticLikes, addOptimisticLike] = useOptimistic(likes, (prev) => prev + 1)
```

### `use()` hook

Reads promises (suspends until resolved) and context, conditionally. The promise must come from a loader/cache, **not** be created during render:

```tsx
function Comments({ commentsPromise }: { commentsPromise: Promise<Comment[]> }) {
  const comments = use(commentsPromise) // parent wraps this in <Suspense>
  return <ul>{comments.map((c) => <li key={c.id}>{c.text}</li>)}</ul>
}
```

### Activity (19.2, stable)

Preserve the state of hidden UI. Hidden children keep state and DOM but unmount effects. The API is `mode="visible" | "hidden"`:

```tsx
{tabs.map((tab) => (
  <Activity key={tab.id} mode={activeTab === tab.id ? "visible" : "hidden"}>
    <tab.component />
  </Activity>
))}
```

`hidden` hides via `display: none`, cleans up effects, preserves state, and pre-renders children at low priority for faster reveals. DOM side effects (video/audio) persist when hidden - add `useLayoutEffect` cleanup if needed.

### useEffectEvent (19.2, stable)

Extract non-reactive logic from effects. The event function always sees the latest props/state without being an effect dependency:

```tsx
function ChatRoom({ roomId, theme }: { roomId: string; theme: string }) {
  const onConnected = useEffectEvent(() => showNotification("Connected!", theme))
  useEffect(() => {
    const conn = createConnection(roomId)
    conn.on("connected", () => onConnected())
    conn.connect()
    return () => conn.disconnect()
  }, [roomId]) // theme is NOT a dep - it's read via the effect event
}
```

Rules: only call from inside effects/other effect events, never pass to children or list in dependency arrays, never call during render. (`useExhaustiveDependencies` in Biome and the react-hooks ESLint rule both understand it - upgrade to the latest plugin version.)

### `<ViewTransition>` (19.3, stable)

Animate UI changes with the browser View Transitions API. Wrap what should animate; only updates inside a Transition (`startTransition`, `useDeferredValue`, Suspense reveals) trigger it - "updates not marked as Transitions don't trigger animations." DOM only.

```tsx
import { ViewTransition, addTransitionType, startTransition } from "react"

<ViewTransition update="auto" default="none">
  <Suspense fallback={<Skeleton />}><Feed /></Suspense>
</ViewTransition>

startTransition(() => {
  addTransitionType("navigate-forward")   // tag the transition so CSS can pick an animation
  setPage(next)
})
```

### Fragment refs (19.3)

Pass a `ref` to `<Fragment>` to get a `FragmentInstance` - add event listeners, observe, or focus across a group of children without a wrapper `<div>`:

```tsx
const ref = useRef<React.FragmentInstance>(null)   // DOM methods typed via @types/react-dom
<Fragment ref={ref}><Item /><Item /></Fragment>
```

### `use(browser())` (19.3)

`browser()` (`import { browser } from "react-dom"`) is a resource for `use()`: "A component can call `use(browser())` to opt out of server-side rendering" - it renders the nearest Suspense fallback on the server and renders for real on the client. Replaces the `useEffect`-mounted-flag pattern for client-only widgets.

### Document metadata

Render `<title>`, `<meta>`, `<link>` directly in components - React hoists them to `<head>`:

```tsx
<title>{post.title}</title>
<meta name="description" content={post.excerpt} />
<link rel="canonical" href={`https://example.com/posts/${post.slug}`} />
```

### Context as provider, ref cleanup

```tsx
<ThemeContext value="dark">{children}</ThemeContext>   // no .Provider

<div ref={(node) => {
  const observer = new ResizeObserver(handleResize)
  if (node) observer.observe(node)
  return () => observer.disconnect()                    // cleanup return
}} />
```

## React Compiler

`babel-plugin-react-compiler` (stable **1.0**) analyzes code at build time and inserts memoization, replacing manual `useMemo`/`useCallback`/`memo` in most cases.

### Setup with Vite

`@vitejs/plugin-react` v6 **removed** the inline `babel` option, so the compiler runs through `@rolldown/plugin-babel`:

```ts
import react, { reactCompilerPreset } from '@vitejs/plugin-react'
import babel from '@rolldown/plugin-babel'

plugins: [react(), babel({ presets: [reactCompilerPreset()] })]
```

```bash
pnpm add -D --save-exact babel-plugin-react-compiler
pnpm add -D @rolldown/plugin-babel @babel/core @types/babel__core
```

`reactCompilerPreset({ compilationMode: 'annotation' })` compiles only components marked `"use memo"`; `target: '17' | '18'` supports older React (needs `react-compiler-runtime`).

**Experimental native compiler (plugin-react 6.1+):** `react({ compiler: true })` runs the compiler in Rust via Oxc, no Babel. Install trap: its peer is `oxc-transform-react ^0.152.0`, so `pnpm add -D oxc-transform-react@latest` can fail with ERESOLVE once a newer minor ships - install the version the peer range names (`oxc-transform-react@0.152`). The old `compiler.logDiagnostics` option is deprecated in favor of `compiler.reportDiagnostics`. Stay on the Babel path for production until this graduates.

### ESLint integration

The compiler's lint rules now ship **inside `eslint-plugin-react-hooks`** (v7.1, flat config by default, ESLint 10 supported): `recommended` carries the stable rules, `recommended-latest` adds the newest compiler-powered ones. If you lint with Biome instead, its nursery `useReactCompiler` rule surfaces the same compiler diagnostics (see [biome.md](biome.md)). The standalone `eslint-plugin-react-compiler` is merged in - remove it if present. New compiler-powered rules catch things like `setState` in render (`set-state-in-render`).

### What not to do

```tsx
// Don't - the compiler handles all of this
const Memo = memo(MyComponent)
const value = useMemo(() => expensive(data), [data])
const cb = useCallback(() => handler(id), [id])
```

Manual memoization still applies when you need a **stable value as an effect dependency**, or a value shared across many components (the compiler memoizes per-component). Opt a component out with the `"use no memo"` directive. Optimized components show a "Memo ✨" badge in React DevTools.

## Worth knowing (newer surface)

- **Partial Pre-rendering (19.2, stable)**: pre-render the static shell of a page, then finish it at request time. New react-dom APIs `prerender` (produce a prelude + a resumable state) and `resume`/`resumeToPipeableStream`/`resumeAndPrerender` continue rendering where the prerender left off. This is a framework/SSR-layer feature - reach for it through your framework, not hand-wired in an SPA.
- **19.3 behavior changes:** Transitions now render independently instead of entangling into one render; StrictMode double-invokes effects during hydration (matching client roots); a DEV warning fires when a library calls `use()` to suspend but skips `use()` once its cache is warm.
- **Trusted Types**: React passes `TrustedHTML`/`TrustedScript` values through without coercion. Server Components can render `<Context>` imported from a `'use client'` module directly.
- **RSC security:** GHSA-wx67-qw84-cm4g (CVE-2026-44907, DoS in Server Functions) affects `react-server-dom-webpack`/`-parcel`/`-turbopack` 19.0.0-19.0.7, 19.1.0-19.1.8, 19.2.0-19.2.7; fixed in 19.0.8/19.1.9/19.2.8 and 19.3. Pure client SPAs are unaffected.
- **`cacheSignal`** (RSC) tells you when a `cache()` lifetime is over.
- **`captureOwnerStack()`** (dev-only) returns the component owner stack for better debugging.
- **Performance Tracks**: React 19.2 adds Scheduler/Components tracks to Chrome DevTools profiles.
- **`useDeferredValue`** gained an `initialValue` option.

## Resources

- React 19.3 blog: https://react.dev/blog/2026/09/09/react-19-3 - 19.2 blog: https://react.dev/blog/2025/10/01/react-19-2
- React Compiler: https://react.dev/learn/react-compiler
- Compiler 1.0: https://react.dev/blog/2025/10/07/react-compiler-1
- API reference: https://react.dev/reference/react
