# React 19 / 19.2 Feature Reference

Complete reference for React 19 (December 2024), React 19.1 (June 2025), and React 19.2 (October 2025) features with TypeScript examples.

## Actions

Actions are async functions used in transitions. They automatically manage pending state, error handling, optimistic updates, and form resets.

### useTransition with Async Functions

```tsx
function PublishButton({ articleId }: { articleId: string }) {
  const [isPending, startTransition] = useTransition()

  const handlePublish = () => {
    startTransition(async () => {
      const result = await publishArticle(articleId)
      if (result.error) {
        toast.error(result.error)
        return
      }
      toast.success("Published!")
    })
  }

  return (
    <button onClick={handlePublish} disabled={isPending}>
      {isPending ? "Publishing..." : "Publish"}
    </button>
  )
}
```

### useActionState

Wraps an action function to track its last result and pending state. Designed for forms:

```tsx
import { useActionState } from "react"

type FormState = {
  errors: Record<string, string[]>
  message: string
} | null

function ContactForm() {
  const [state, submitAction, isPending] = useActionState<FormState, FormData>(
    async (previousState, formData) => {
      const name = formData.get("name") as string
      const email = formData.get("email") as string

      if (!name) return { errors: { name: ["Name is required"] }, message: "" }
      if (!email) return { errors: { email: ["Email is required"] }, message: "" }

      const result = await submitContact({ name, email })
      if (result.error) {
        return { errors: {}, message: result.error }
      }
      return null // success - resets form (uncontrolled components)
    },
    null
  )

  return (
    <form action={submitAction}>
      <div>
        <input name="name" placeholder="Name" />
        {state?.errors.name?.map((e, i) => <p key={i} className="text-destructive text-sm">{e}</p>)}
      </div>
      <div>
        <input name="email" type="email" placeholder="Email" />
        {state?.errors.email?.map((e, i) => <p key={i} className="text-destructive text-sm">{e}</p>)}
      </div>
      {state?.message && <p className="text-destructive">{state.message}</p>}
      <button type="submit" disabled={isPending}>
        {isPending ? "Sending..." : "Send"}
      </button>
    </form>
  )
}
```

### Form Actions

`<form>` elements accept functions as `action` prop. The form auto-resets on success for uncontrolled components:

```tsx
function SearchForm({ onSearch }: { onSearch: (query: string) => Promise<void> }) {
  return (
    <form action={async (formData: FormData) => {
      await onSearch(formData.get("q") as string)
    }}>
      <input name="q" type="search" placeholder="Search..." />
      <button type="submit">Search</button>
    </form>
  )
}
```

### useFormStatus

Access the pending state of a parent `<form>` from a child component:

```tsx
import { useFormStatus } from "react-dom"

function SubmitButton({ children }: { children: React.ReactNode }) {
  const { pending, data, method, action } = useFormStatus()
  return (
    <button type="submit" disabled={pending}>
      {pending ? "Submitting..." : children}
    </button>
  )
}

// Usage - SubmitButton reads state from nearest parent <form>
function MyForm() {
  return (
    <form action={myAction}>
      <input name="field" />
      <SubmitButton>Save</SubmitButton>
    </form>
  )
}
```

### useOptimistic

Show optimistic state while an async action is in flight:

```tsx
import { useOptimistic } from "react"

type Message = { id: string; text: string; sending?: boolean }

function Chat({ messages, sendMessage }: {
  messages: Message[]
  sendMessage: (text: string) => Promise<void>
}) {
  const [optimisticMessages, addOptimistic] = useOptimistic(
    messages,
    (current: Message[], newText: string) => [
      ...current,
      { id: crypto.randomUUID(), text: newText, sending: true },
    ]
  )

  const formAction = async (formData: FormData) => {
    const text = formData.get("message") as string
    addOptimistic(text)
    await sendMessage(text)
  }

  return (
    <div>
      {optimisticMessages.map(msg => (
        <p key={msg.id} style={{ opacity: msg.sending ? 0.5 : 1 }}>
          {msg.text}
        </p>
      ))}
      <form action={formAction}>
        <input name="message" />
        <button type="submit">Send</button>
      </form>
    </div>
  )
}
```

## use() Hook

`use()` reads resources in render. Unlike hooks, it can be called conditionally.

### Reading Promises

```tsx
import { use, Suspense } from "react"

type Product = { id: string; name: string; price: number }

function ProductDetails({ productPromise }: { productPromise: Promise<Product> }) {
  const product = use(productPromise) // suspends until resolved
  return (
    <div>
      <h2>{product.name}</h2>
      <p>${product.price.toFixed(2)}</p>
    </div>
  )
}

// Promise MUST come from outside render (loader, cache, server function)
function ProductPage({ productPromise }: { productPromise: Promise<Product> }) {
  return (
    <Suspense fallback={<ProductSkeleton />}>
      <ProductDetails productPromise={productPromise} />
    </Suspense>
  )
}
```

**Critical:** Never create promises inside the component that calls `use()`. The promise must come from a cached source, a loader, or a server function. Creating promises in render causes infinite suspense loops.

### Reading Context Conditionally

```tsx
import { use, createContext } from "react"

const FeatureFlagsContext = createContext<Record<string, boolean>>({})

function FeatureGate({ flag, children }: { flag: string; children: React.ReactNode }) {
  const flags = use(FeatureFlagsContext)
  if (!flags[flag]) return null
  return <>{children}</>
}

function ConditionalContextRead({ user }: { user: User | null }) {
  if (!user) return <LoginScreen />

  // This is fine - use() can be called after early returns
  const permissions = use(PermissionsContext)
  return <Dashboard user={user} permissions={permissions} />
}
```

### use() vs useContext()

| Feature | `use()` | `useContext()` |
|---------|---------|---------------|
| Call after early return | Yes | No |
| Call in loops/conditionals | Yes | No |
| Read promises | Yes | No |
| Read context | Yes | Yes |
| Must be in component/hook | Yes | Yes |

## Activity Component (React 19.2)

`<Activity>` controls component visibility while preserving state. Hidden children keep their state and DOM but unmount effects.

### Modes

- **`visible`** (default) - renders normally, effects mounted, updates processed normally
- **`hidden`** - hides via `display: none`, effects cleaned up, state preserved, updates deferred to idle time

### State Preservation with Tabs

```tsx
import { Activity, useState, Suspense } from "react"

type Tab = { id: string; label: string; component: React.ComponentType }

function TabContainer({ tabs }: { tabs: Tab[] }) {
  const [activeTab, setActiveTab] = useState(tabs[0].id)

  return (
    <>
      <div role="tablist">
        {tabs.map(tab => (
          <button
            key={tab.id}
            role="tab"
            aria-selected={activeTab === tab.id}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <Suspense fallback={<TabSkeleton />}>
        {tabs.map(tab => (
          <Activity key={tab.id} mode={activeTab === tab.id ? "visible" : "hidden"}>
            <div role="tabpanel">
              <tab.component />
            </div>
          </Activity>
        ))}
      </Suspense>
    </>
  )
}
```

### Pre-rendering Hidden Content

Render content the user is likely to navigate to next at low priority:

```tsx
function WizardForm() {
  const [step, setStep] = useState(1)

  return (
    <>
      <Activity mode={step === 1 ? "visible" : "hidden"}>
        <StepOne onNext={() => setStep(2)} />
      </Activity>
      <Activity mode={step === 2 ? "visible" : "hidden"}>
        <StepTwo onBack={() => setStep(1)} onNext={() => setStep(3)} />
      </Activity>
      {/* Pre-render step 3 - data loads in background */}
      <Activity mode={step === 3 ? "visible" : "hidden"}>
        <Suspense fallback={<Skeleton />}>
          <StepThree onBack={() => setStep(2)} />
        </Suspense>
      </Activity>
    </>
  )
}
```

### Handling DOM Side Effects

Hidden Activity preserves DOM, so elements like `<video>` keep playing. Add effect cleanup:

```tsx
import { useRef, useLayoutEffect } from "react"

function VideoPlayer({ src }: { src: string }) {
  const videoRef = useRef<HTMLVideoElement>(null)

  // useLayoutEffect cleanup runs when Activity hides
  useLayoutEffect(() => {
    const video = videoRef.current
    return () => {
      video?.pause() // pause when hidden by Activity
    }
  }, [])

  return <video ref={videoRef} src={src} controls playsInline />
}
```

### Selective Hydration

Activity boundaries participate in selective hydration. Always-visible Activity improves hydration performance by letting React prioritize interactive elements:

```tsx
function Page() {
  return (
    <>
      <Header /> {/* hydrates first - interactive controls */}
      <Activity>
        <HeavyContentSection /> {/* hydrates independently, at lower priority */}
      </Activity>
    </>
  )
}
```

## useEffectEvent (React 19.2)

Separates non-reactive event logic from effects. The event function always reads the latest props/state without re-triggering the effect.

### Basic Pattern

```tsx
import { useEffect, useEffectEvent } from "react"

function AnalyticsTracker({ pageUrl, userId }: { pageUrl: string; userId: string }) {
  // onVisit always sees latest userId without re-running the effect
  const onVisit = useEffectEvent(() => {
    trackPageView(pageUrl, userId)
  })

  useEffect(() => {
    onVisit()
    // Only re-run when pageUrl changes, not userId
  }, [pageUrl])
}
```

### Timer with Latest Values

```tsx
function Poller({ interval, endpoint, onData }: {
  interval: number
  endpoint: string
  onData: (data: unknown) => void
}) {
  const onPoll = useEffectEvent(async () => {
    const data = await fetch(endpoint).then(r => r.json())
    onData(data) // always calls latest onData
  })

  useEffect(() => {
    const id = setInterval(() => onPoll(), interval)
    return () => clearInterval(id)
  }, [interval]) // endpoint and onData changes don't restart interval
}
```

### Custom Hook with useEffectEvent

```tsx
function useDocumentTitle(title: string, options?: { restoreOnUnmount?: boolean }) {
  const onRestore = useEffectEvent(() => {
    if (options?.restoreOnUnmount) {
      document.title = previousTitle.current
    }
  })

  const previousTitle = useRef(document.title)

  useEffect(() => {
    document.title = title
    return () => onRestore()
  }, [title])
}
```

### Rules and Restrictions

1. Only call from inside `useEffect`, `useLayoutEffect`, `useInsertionEffect`, or other effect events
2. Never include in dependency arrays - they are intentionally not stable
3. Never call during render
4. Never pass to child components
5. Must be declared in the same component or hook as the effect that uses it

## ref as Prop

`forwardRef` is no longer needed. `ref` is a regular prop in React 19:

```tsx
// Component receiving ref
function TextInput({ placeholder, ref, ...props }: React.ComponentProps<"input">) {
  return <input ref={ref} placeholder={placeholder} {...props} />
}

// Parent using ref
function Form() {
  const inputRef = useRef<HTMLInputElement>(null)
  return (
    <>
      <TextInput ref={inputRef} placeholder="Enter text" />
      <button onClick={() => inputRef.current?.focus()}>Focus</button>
    </>
  )
}
```

### Ref Cleanup Functions

```tsx
function AutoFocusInput() {
  return (
    <input
      ref={(node) => {
        if (node) {
          node.focus()
          // Return cleanup function - called on unmount
          return () => {
            // cleanup logic
          }
        }
      }}
    />
  )
}
```

**TypeScript note:** Returning anything from a ref callback is now treated as a cleanup function. Use explicit block bodies to avoid accidental returns:

```tsx
// WRONG - implicit return of HTMLElement
<div ref={current => (instance = current)} />

// CORRECT - block body, no return
<div ref={current => { instance = current }} />
```

## Context as Provider

`<Context.Provider>` is replaced by using the context directly:

```tsx
const ThemeContext = createContext<"light" | "dark">("light")

// React 19 - context IS the provider
function App({ children }: { children: React.ReactNode }) {
  const [theme, setTheme] = useState<"light" | "dark">("light")
  return (
    <ThemeContext value={theme}>
      {children}
    </ThemeContext>
  )
}

// <ThemeContext.Provider> still works but will be deprecated
```

## Document Metadata

React 19 hoists `<title>`, `<meta>`, and `<link>` tags to `<head>` automatically:

```tsx
function ProductPage({ product }: { product: Product }) {
  return (
    <>
      <title>{product.name} - MyStore</title>
      <meta name="description" content={product.description} />
      <meta property="og:title" content={product.name} />
      <meta property="og:image" content={product.imageUrl} />
      <link rel="canonical" href={`https://mystore.com/products/${product.slug}`} />

      <article>
        <h1>{product.name}</h1>
        <p>{product.description}</p>
      </article>
    </>
  )
}
```

Works with client-only apps, streaming SSR, and Server Components. For complex metadata needs (route-based overrides), consider a metadata library.

## Stylesheet Support

React 19 manages stylesheet loading and ordering:

```tsx
function FeatureSection() {
  return (
    <Suspense fallback={<Skeleton />}>
      {/* React ensures stylesheet loads before revealing content */}
      <link rel="stylesheet" href="/styles/feature.css" precedence="default" />
      <div className="feature-content">
        Content that depends on feature.css
      </div>
    </Suspense>
  )
}
```

`precedence` controls insertion order. Duplicate stylesheets are automatically deduplicated.

## Resource Preloading

```tsx
import { prefetchDNS, preconnect, preload, preinit } from "react-dom"

function AppShell() {
  // Preload critical resources
  preinit("/scripts/analytics.js", { as: "script" })
  preload("/fonts/inter.woff2", { as: "font", type: "font/woff2", crossOrigin: "anonymous" })
  preconnect("https://api.example.com")
  prefetchDNS("https://cdn.example.com")

  return <App />
}
```

## useDeferredValue with Initial Value

```tsx
function Search({ query }: { query: string }) {
  // First render returns "" (instant), then schedules re-render with actual query
  const deferredQuery = useDeferredValue(query, "")

  return (
    <Suspense fallback={<SearchSkeleton />}>
      <SearchResults query={deferredQuery} />
    </Suspense>
  )
}
```

## Error Handling Improvements

### Error Boundary with onCaughtError

```tsx
import { createRoot } from "react-dom/client"

const root = createRoot(document.getElementById("root")!, {
  onCaughtError: (error, errorInfo) => {
    // Error caught by an Error Boundary
    reportToErrorService(error, errorInfo.componentStack)
  },
  onUncaughtError: (error, errorInfo) => {
    // Error NOT caught by any Error Boundary
    showCrashDialog(error)
  },
  onRecoverableError: (error, errorInfo) => {
    // Error that React recovered from automatically
    console.warn("Recoverable:", error)
  },
})
```

## Hydration Improvements

React 19 provides clear diff output for hydration mismatches instead of cryptic errors. Third-party scripts and browser extensions that inject elements into `<head>` and `<body>` no longer trigger mismatch errors.

## Performance Tracks (React 19.2)

Custom tracks in Chrome DevTools performance profiles:

- **Scheduler track** - shows what React is working on per priority (blocking, transition)
- **Components track** - shows component render and effect timing in a tree view

Enable by recording a performance profile in Chrome DevTools - the tracks appear automatically in React 19.2+ apps.

## cacheSignal (React 19.2, RSC only)

For React Server Components, `cacheSignal()` provides an `AbortSignal` tied to the `cache()` lifetime:

```tsx
import { cache, cacheSignal } from "react"

const fetchData = cache(async (url: string) => {
  const response = await fetch(url, { signal: cacheSignal() })
  return response.json()
})
```

The signal aborts when the cache entry is no longer needed (render failed, aborted, or completed).

## Partial Pre-rendering (React 19.2)

Pre-render static shell, resume dynamic content later:

```tsx
import { prerender } from "react-dom/static"
import { resume } from "react-dom/server"

// Step 1: Pre-render at build time
const { prelude, postponed } = await prerender(<App />, {
  signal: controller.signal,
})
await savePostponedState(postponed)

// Step 2: Resume at request time
const postponedState = await getPostponedState(request)
const stream = await resume(<App />, postponedState)
```

## eslint-plugin-react-hooks v6

Ships with React 19.2. Flat config by default. The `recommended` preset includes React Compiler-powered lint rules:

```js
// eslint.config.js
import reactHooks from "eslint-plugin-react-hooks"

export default [
  reactHooks.configs.recommended, // includes compiler rules in v6+
]
```
