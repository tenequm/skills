# TypeScript Patterns for React

Advanced TypeScript patterns, utility types, strict configuration, and type-level programming for React applications. Targets TypeScript 5.9.

## Strict tsconfig Reference

### Recommended Config for React + Vite

```jsonc
{
  "compilerOptions": {
    // Environment
    "target": "esnext",
    "module": "nodenext",
    "moduleDetection": "force",
    "jsx": "react-jsx",
    "lib": ["esnext", "dom", "dom.iterable"],

    // Module behavior
    "verbatimModuleSyntax": true,
    "isolatedModules": true,
    "noUncheckedSideEffectImports": true,

    // Strictness
    "strict": true,
    "noUncheckedIndexedAccess": true,
    "exactOptionalPropertyTypes": true,

    // Output
    "sourceMap": true,
    "declaration": true,
    "declarationMap": true,
    "skipLibCheck": true,

    // Limit ambient types
    "types": []
  },
  "include": ["src"]
}
```

### What Each Strict Option Does

| Option | Effect |
|--------|--------|
| `strict` | Enables `strictNullChecks`, `strictFunctionTypes`, `strictBindCallApply`, `strictPropertyInitialization`, `noImplicitAny`, `noImplicitThis`, `alwaysStrict`, `useUnknownInCatchVariables` |
| `noUncheckedIndexedAccess` | Array/object index access returns `T \| undefined` instead of `T` |
| `exactOptionalPropertyTypes` | `{ x?: string }` means `string \| undefined` but NOT assignable to `string \| undefined` explicitly - must use `?:` |
| `verbatimModuleSyntax` | Forces `import type` for type-only imports, prevents import elision bugs |
| `noUncheckedSideEffectImports` | Errors on `import "./styles.css"` if the file doesn't exist |

### When to Use `module: "nodenext"` vs `"node20"`

- **`nodenext`** - floating target, follows latest Node.js behavior. Implies `target: esnext`. Supports `require()` of ESM (Node 22+).
- **`node20`** - stable, models Node.js 20 behavior. Implies `target: es2023`. Does NOT support `require()` of ESM.

For app development with modern bundlers (Vite), `nodenext` is the best choice. For libraries targeting Node 20+, `node20` provides stability.

## TypeScript 5.9 Features

### import defer

Defers module evaluation until a property is accessed. Only namespace imports allowed:

```tsx
// Module is loaded but NOT executed until accessed
import defer * as analytics from "./analytics.js"

function handleClick() {
  // analytics module evaluates here, on first property access
  analytics.track("click", { target: "button" })
}
```

Only works with `--module preserve` or `--module esnext`. Not transformed by TypeScript - requires runtime/bundler support.

### --module node20

Stable module target for Node.js 20 behavior:

```jsonc
{
  "compilerOptions": {
    "module": "node20" // stable, implies target: es2023
  }
}
```

Unlike `nodenext`, `node20` won't change behavior in future TS releases.

### Expandable Hovers (Preview)

VS Code quick info tooltips now show `+`/`-` buttons to expand/collapse type details inline. Configure max length with `js/ts.hover.maximumLength` setting.

### Minimal tsc --init

`tsc --init` now generates a lean tsconfig with modern defaults instead of a commented-out wall of options. Includes `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, and `jsx: "react-jsx"` by default.

### Performance: Cached Type Instantiations

Complex generic libraries (Zod, tRPC) benefit from cached intermediate type instantiations, reducing "excessive type instantiation depth" errors.

## TypeScript 5.8 Features

### Granular Branch Checks in Return Expressions

TypeScript 5.8 checks each branch of conditional returns against the declared return type:

```tsx
declare const cache: Map<any, any>

function getUrl(input: string): URL {
  return cache.has(input)
    ? cache.get(input)
    : input
  //  ~~~~~ Error: Type 'string' is not assignable to type 'URL'
  // Previously this was hidden because `any | string` simplified to `any`
}
```

### require() of ESM (--module nodenext)

Node.js 22+ allows `require()` of ESM modules. TypeScript 5.8 supports this under `--module nodenext`:

```tsx
// CommonJS file can now require ESM modules (Node 22+)
const { helper } = require("./esm-module.js")
```

### --erasableSyntaxOnly

For Node.js type stripping (`--experimental-strip-types`), ensures no TypeScript constructs with runtime semantics:

```jsonc
{
  "compilerOptions": {
    "erasableSyntaxOnly": true // errors on enums, namespaces, parameter properties
  }
}
```

## Component Props Patterns

### Basic Pattern - Extend Native Props

```tsx
type ButtonProps = React.ComponentProps<"button"> & {
  variant?: "primary" | "secondary" | "ghost"
  size?: "sm" | "md" | "lg"
  isLoading?: boolean
}

function Button({ variant = "primary", size = "md", isLoading, children, disabled, ...props }: ButtonProps) {
  return (
    <button
      data-slot="button"
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? <Spinner /> : children}
    </button>
  )
}
```

### Children Types

```tsx
// Any renderable React content
type Props = { children: React.ReactNode }

// Only a single element
type Props = { children: React.ReactElement }

// Render prop pattern
type Props = { children: (data: User) => React.ReactNode }

// No children allowed
type Props = { children?: never }
```

### Discriminated Union Props

```tsx
type AlertProps =
  | { variant: "info"; message: string }
  | { variant: "action"; message: string; onAction: () => void; actionLabel: string }
  | { variant: "dismissible"; message: string; onDismiss: () => void }

function Alert(props: AlertProps) {
  switch (props.variant) {
    case "info":
      return <div className="alert-info">{props.message}</div>
    case "action":
      return (
        <div className="alert-action">
          {props.message}
          <button onClick={props.onAction}>{props.actionLabel}</button>
        </div>
      )
    case "dismissible":
      return (
        <div className="alert-dismiss">
          {props.message}
          <button onClick={props.onDismiss}>Dismiss</button>
        </div>
      )
  }
}
```

### Polymorphic Components

```tsx
type PolymorphicProps<E extends React.ElementType, P = object> = P &
  Omit<React.ComponentProps<E>, keyof P | "as"> & {
    as?: E
  }

function Box<E extends React.ElementType = "div">({
  as,
  ...props
}: PolymorphicProps<E>) {
  const Component = as || "div"
  return <Component {...props} />
}

// Usage
<Box>div by default</Box>
<Box as="section">renders section</Box>
<Box as="a" href="/about">renders anchor with href prop</Box>
<Box as={Link} to="/about">renders Link component</Box>
```

### Slot Pattern

```tsx
type SlotProps<E extends React.ElementType = "div"> = {
  asChild?: boolean
  children: React.ReactElement
} & React.ComponentProps<E>

// Used by libraries like Radix UI for composition
```

## Generic Components

### Generic List

```tsx
type ListProps<T> = {
  items: T[]
  renderItem: (item: T, index: number) => React.ReactNode
  keyExtractor: (item: T) => string
  emptyState?: React.ReactNode
}

function List<T>({ items, renderItem, keyExtractor, emptyState }: ListProps<T>) {
  if (items.length === 0) return <>{emptyState ?? <p>No items</p>}</>
  return (
    <ul>
      {items.map((item, i) => (
        <li key={keyExtractor(item)}>{renderItem(item, i)}</li>
      ))}
    </ul>
  )
}

// T inferred as User
<List
  items={users}
  renderItem={(user) => <span>{user.name}</span>}
  keyExtractor={(user) => user.id}
/>
```

### Generic Select

```tsx
type SelectOption<T> = {
  value: T
  label: string
}

type SelectProps<T> = {
  options: SelectOption<T>[]
  value: T
  onChange: (value: T) => void
  placeholder?: string
}

function Select<T extends string | number>({
  options,
  value,
  onChange,
  placeholder,
}: SelectProps<T>) {
  return (
    <select
      value={String(value)}
      onChange={(e) => {
        const option = options.find(o => String(o.value) === e.target.value)
        if (option) onChange(option.value)
      }}
    >
      {placeholder && <option value="">{placeholder}</option>}
      {options.map(opt => (
        <option key={String(opt.value)} value={String(opt.value)}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
```

### Generic Table

```tsx
type Column<T> = {
  key: string
  header: string
  render: (item: T) => React.ReactNode
  width?: string
}

type TableProps<T> = {
  data: T[]
  columns: Column<T>[]
  keyExtractor: (item: T) => string
  onRowClick?: (item: T) => void
}

function Table<T>({ data, columns, keyExtractor, onRowClick }: TableProps<T>) {
  return (
    <table>
      <thead>
        <tr>
          {columns.map(col => (
            <th key={col.key} style={{ width: col.width }}>{col.header}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map(item => (
          <tr key={keyExtractor(item)} onClick={() => onRowClick?.(item)}>
            {columns.map(col => (
              <td key={col.key}>{col.render(item)}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

## Hook Types

### Custom Hook Return Types

```tsx
// Tuple return - use `as const` or explicit tuple
function useToggle(initial = false): [boolean, () => void, (value: boolean) => void] {
  const [value, setValue] = useState(initial)
  const toggle = () => setValue(v => !v)
  return [value, toggle, setValue]
}

// Object return - better for hooks with many values
function useAsync<T>(asyncFn: () => Promise<T>) {
  const [state, setState] = useState<{
    status: "idle" | "loading" | "success" | "error"
    data: T | null
    error: Error | null
  }>({ status: "idle", data: null, error: null })

  const execute = async () => {
    setState({ status: "loading", data: null, error: null })
    try {
      const data = await asyncFn()
      setState({ status: "success", data, error: null })
    } catch (error) {
      setState({ status: "error", data: null, error: error as Error })
    }
  }

  return { ...state, execute }
}
```

### Typed useReducer

```tsx
type State = {
  items: Item[]
  filter: string
  sortBy: "name" | "date" | "priority"
  sortOrder: "asc" | "desc"
}

type Action =
  | { type: "SET_FILTER"; filter: string }
  | { type: "SET_SORT"; sortBy: State["sortBy"]; sortOrder?: State["sortOrder"] }
  | { type: "ADD_ITEM"; item: Item }
  | { type: "REMOVE_ITEM"; id: string }
  | { type: "RESET" }

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "SET_FILTER":
      return { ...state, filter: action.filter }
    case "SET_SORT":
      return { ...state, sortBy: action.sortBy, sortOrder: action.sortOrder ?? state.sortOrder }
    case "ADD_ITEM":
      return { ...state, items: [...state.items, action.item] }
    case "REMOVE_ITEM":
      return { ...state, items: state.items.filter(i => i.id !== action.id) }
    case "RESET":
      return initialState
  }
}
```

### Typed Context with Factory Hook

```tsx
import { createContext, use, useState } from "react"

type AuthState = {
  user: User | null
  login: (credentials: Credentials) => Promise<void>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthState | null>(null)

function useAuth(): AuthState {
  const ctx = use(AuthContext)
  if (!ctx) throw new Error("useAuth must be used within AuthProvider")
  return ctx
}

function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)

  const auth: AuthState = {
    user,
    isAuthenticated: user !== null,
    login: async (credentials) => {
      const user = await authenticate(credentials)
      setUser(user)
    },
    logout: () => setUser(null),
  }

  return <AuthContext value={auth}>{children}</AuthContext>
}
```

## Utility Types for React

### Extract Props from Components

```tsx
// Get props type from any component
type ButtonProps = React.ComponentProps<typeof Button>

// Get props from native elements
type InputProps = React.ComponentProps<"input">

// Get ref type from element
type DivRef = React.ComponentRef<"div"> // HTMLDivElement
```

### Strict Omit

```tsx
// Built-in Omit allows omitting keys that don't exist
// StrictOmit ensures keys exist on the type
type StrictOmit<T, K extends keyof T> = Omit<T, K>

type UserWithoutId = StrictOmit<User, "id"> // OK
type UserWithoutFoo = StrictOmit<User, "foo"> // Error: "foo" not in keyof User
```

### DeepPartial for Form Defaults

```tsx
type DeepPartial<T> = T extends object
  ? { [P in keyof T]?: DeepPartial<T[P]> }
  : T

type FormDefaults = DeepPartial<UserProfile>
// All nested fields become optional
```

### Branded Types

```tsx
type Brand<T, B extends string> = T & { __brand: B }

type UserId = Brand<string, "UserId">
type PostId = Brand<string, "PostId">

function getUser(id: UserId): Promise<User> { /* ... */ }
function getPost(id: PostId): Promise<Post> { /* ... */ }

const userId = "abc" as UserId
const postId = "xyz" as PostId

getUser(userId) // OK
getUser(postId) // Error: PostId is not assignable to UserId
```

### Record with Exhaustive Keys

```tsx
// Ensure all enum/union values are covered
type Status = "draft" | "published" | "archived"

const statusLabels: Record<Status, string> = {
  draft: "Draft",
  published: "Published",
  archived: "Archived",
  // If you add a new status, TypeScript errors here until you add its label
}

const statusColors = {
  draft: "text-muted-foreground",
  published: "text-success",
  archived: "text-destructive",
} satisfies Record<Status, string>
```

## Type-Safe Event Patterns

### Custom Events with Discriminated Unions

```tsx
type AppEvent =
  | { type: "navigate"; path: string }
  | { type: "notification"; message: string; level: "info" | "error" }
  | { type: "auth"; action: "login" | "logout"; userId?: string }

type EventHandler<T extends AppEvent["type"]> = (
  event: Extract<AppEvent, { type: T }>
) => void

function useEventBus() {
  const handlers = useRef(new Map<string, Set<Function>>())

  const on = <T extends AppEvent["type"]>(type: T, handler: EventHandler<T>) => {
    if (!handlers.current.has(type)) handlers.current.set(type, new Set())
    handlers.current.get(type)!.add(handler)
    return () => { handlers.current.get(type)?.delete(handler) }
  }

  const emit = (event: AppEvent) => {
    handlers.current.get(event.type)?.forEach(fn => fn(event))
  }

  return { on, emit }
}
```

## Type Narrowing Patterns

### Exhaustive Switch with never

```tsx
type Shape =
  | { kind: "circle"; radius: number }
  | { kind: "rectangle"; width: number; height: number }
  | { kind: "triangle"; base: number; height: number }

function area(shape: Shape): number {
  switch (shape.kind) {
    case "circle": return Math.PI * shape.radius ** 2
    case "rectangle": return shape.width * shape.height
    case "triangle": return 0.5 * shape.base * shape.height
    default: {
      const _exhaustive: never = shape
      throw new Error(`Unhandled shape: ${_exhaustive}`)
    }
  }
}
```

### Type Guards

```tsx
// Type predicate
function isUser(value: unknown): value is User {
  return (
    typeof value === "object" &&
    value !== null &&
    "id" in value &&
    "name" in value &&
    typeof (value as User).id === "string"
  )
}

// Assertion function
function assertDefined<T>(value: T | null | undefined, message?: string): asserts value is T {
  if (value == null) throw new Error(message ?? "Expected value to be defined")
}

// Usage
const user = getUser(id)
assertDefined(user, `User ${id} not found`)
user.name // typed as User, no null check needed
```

### Narrowing with in operator

```tsx
type ApiResponse =
  | { data: User[]; pagination: Pagination }
  | { error: string; code: number }

function handleResponse(response: ApiResponse) {
  if ("error" in response) {
    console.error(`Error ${response.code}: ${response.error}`)
    return
  }
  // TypeScript knows this is the success variant
  console.log(`Got ${response.data.length} users, page ${response.pagination.page}`)
}
```

## satisfies Operator

### Config Objects with Literal Preservation

```tsx
const config = {
  apiUrl: "https://api.example.com",
  timeout: 5000,
  retries: 3,
} satisfies Record<string, string | number>

// config.apiUrl is typed as "https://api.example.com" (literal), not string
// But the shape is validated against Record<string, string | number>
```

### Route Definitions

```tsx
type RouteConfig = {
  path: string
  auth?: boolean
}

const routes = {
  home: { path: "/" },
  dashboard: { path: "/dashboard", auth: true },
  settings: { path: "/settings", auth: true },
  login: { path: "/login" },
} satisfies Record<string, RouteConfig>

// routes.home.path is "/", not string
// Object.keys(routes) works with autocomplete
type RouteKey = keyof typeof routes // "home" | "dashboard" | "settings" | "login"
```

### as const satisfies

Combine for maximum type safety:

```tsx
const PERMISSIONS = {
  read: { level: 1, label: "Read" },
  write: { level: 2, label: "Write" },
  admin: { level: 3, label: "Admin" },
} as const satisfies Record<string, { level: number; label: string }>

// Values are readonly with literal types
// Shape is validated
type PermissionKey = keyof typeof PERMISSIONS // "read" | "write" | "admin"
type PermissionLevel = typeof PERMISSIONS[PermissionKey]["level"] // 1 | 2 | 3
```

## Zod v4 Integration Patterns

### Schema-Driven Form Types

```tsx
import { z } from "zod"

const CreateProjectSchema = z.object({
  name: z.string().min(1, "Name is required").max(100),
  description: z.string().optional(),
  visibility: z.enum(["public", "private"]),
  tags: z.array(z.string()).max(10).default([]),
})

type CreateProjectInput = z.input<typeof CreateProjectSchema>  // what the form submits
type CreateProject = z.output<typeof CreateProjectSchema>       // what you get after parsing

// Use z.infer as shorthand for z.output
type CreateProjectInferred = z.infer<typeof CreateProjectSchema>
```

### Validation in Actions

```tsx
// Zod v4: use z.flattenError() for flat field-level errors
type FieldErrors = Partial<Record<keyof CreateProjectInput, string[]>>

function CreateProjectForm() {
  const [errors, action, isPending] = useActionState(
    async (_prev: FieldErrors | null, formData: FormData) => {
      const raw = {
        name: formData.get("name"),
        description: formData.get("description") || undefined,
        visibility: formData.get("visibility"),
        tags: formData.getAll("tags"),
      }

      const result = CreateProjectSchema.safeParse(raw)
      if (!result.success) {
        return z.flattenError(result.error).fieldErrors as FieldErrors
      }

      await createProject(result.data)
      redirect("/projects")
      return null
    },
    null
  )

  return (
    <form action={action}>
      <input name="name" />
      {errors?.name?.map((e, i) => <p key={i}>{e}</p>)}

      <textarea name="description" />

      <select name="visibility">
        <option value="public">Public</option>
        <option value="private">Private</option>
      </select>
      {errors?.visibility?.map((e, i) => <p key={i}>{e}</p>)}

      <button type="submit" disabled={isPending}>Create</button>
    </form>
  )
}
```

## Template Literal Types

### Type-Safe CSS Custom Properties

```tsx
type CSSVar = `--${string}`
type CSSVarValue = `var(${CSSVar})`

function setThemeVar(name: CSSVar, value: string) {
  document.documentElement.style.setProperty(name, value)
}

setThemeVar("--primary", "oklch(0.6 0.2 250)")
setThemeVar("primary", "red") // Error: must start with --
```

### Type-Safe Route Params

```tsx
type ExtractParams<T extends string> =
  T extends `${string}:${infer Param}/${infer Rest}`
    ? Param | ExtractParams<Rest>
    : T extends `${string}:${infer Param}`
      ? Param
      : never

type Params = ExtractParams<"/users/:userId/posts/:postId">
// "userId" | "postId"
```

## Error Handling Patterns

### Result Type

```tsx
type Result<T, E = Error> =
  | { ok: true; value: T }
  | { ok: false; error: E }

function ok<T>(value: T): Result<T, never> {
  return { ok: true, value }
}

function err<E>(error: E): Result<never, E> {
  return { ok: false, error }
}

// Usage
async function fetchUser(id: string): Promise<Result<User, "not_found" | "network_error">> {
  try {
    const res = await fetch(`/api/users/${id}`)
    if (res.status === 404) return err("not_found")
    return ok(await res.json())
  } catch {
    return err("network_error")
  }
}

const result = await fetchUser("123")
if (result.ok) {
  console.log(result.value.name) // User typed
} else {
  console.error(result.error) // "not_found" | "network_error"
}
```

### Typed Error Boundaries

```tsx
import { Component, type ErrorInfo, type ReactNode } from "react"

type ErrorBoundaryProps = {
  children: ReactNode
  fallback: (error: Error, retry: () => void) => ReactNode
  onError?: (error: Error, info: ErrorInfo) => void
}

type ErrorBoundaryState = {
  error: Error | null
}

class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { error: null }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    this.props.onError?.(error, info)
  }

  render() {
    if (this.state.error) {
      return this.props.fallback(this.state.error, () => this.setState({ error: null }))
    }
    return this.props.children
  }
}

// Usage
<ErrorBoundary
  fallback={(error, retry) => (
    <div>
      <p>Something went wrong: {error.message}</p>
      <button onClick={retry}>Try again</button>
    </div>
  )}
  onError={(error, info) => reportError(error, info.componentStack)}
>
  <App />
</ErrorBoundary>
```
