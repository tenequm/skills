
# TanStack Query (React Query) v5

Powerful asynchronous state management for React. TanStack Query makes fetching, caching, synchronizing, and updating server state in your React applications a breeze.

## When to Use This Skill

- Fetching data from REST APIs or GraphQL endpoints
- Managing server state and cache lifecycle
- Implementing mutations (create, update, delete operations)
- Building infinite scroll or load-more patterns
- Handling optimistic UI updates
- Rendering streaming/chunked data from AI or SSE endpoints
- Integrating with tRPC v11 queryOptions pattern
- Synchronizing data across components
- Implementing background data refetching
- Managing complex async state without Redux or other state managers

## Quick Start Workflow

### 1. Installation

```bash
npm install @tanstack/react-query
# or
pnpm add @tanstack/react-query
# or
yarn add @tanstack/react-query
```

### 2. Setup QueryClient

Wrap your application with `QueryClientProvider`:

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
    </QueryClientProvider>
  );
}
```

### 3. Basic Query

```tsx
import { useQuery } from '@tanstack/react-query';

function TodoList() {
  const { data, isLoading, error } = useQuery({
    queryKey: ['todos'],
    queryFn: async () => {
      const res = await fetch('https://api.example.com/todos');
      if (!res.ok) throw new Error('Network response was not ok');
      return res.json();
    },
  });

  if (isLoading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;

  return (
    <ul>
      {data.map((todo) => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  );
}
```

### 4. Basic Mutation

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function CreateTodo() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: async (newTodo) => {
      const res = await fetch('https://api.example.com/todos', {
        method: 'POST',
        body: JSON.stringify(newTodo),
        headers: { 'Content-Type': 'application/json' },
      });
      return res.json();
    },
    onSuccess: () => {
      // Invalidate and refetch todos
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  return (
    <button onClick={() => mutation.mutate({ title: 'New Todo' })}>
      {mutation.isPending ? 'Creating...' : 'Create Todo'}
    </button>
  );
}
```

## Core Concepts

### Query Keys

Query keys uniquely identify queries and are used for caching. They must be arrays.

```tsx
// Simple key
useQuery({ queryKey: ['todos'], queryFn: fetchTodos });

// Key with variables
useQuery({ queryKey: ['todo', todoId], queryFn: () => fetchTodo(todoId) });

// Hierarchical keys
useQuery({ queryKey: ['todos', 'list', { filters, page }], queryFn: fetchTodos });
```

**Query key matching:**
- `['todos']` - exact match
- `['todos', { page: 1 }]` - exact match with object
- `{ queryKey: ['todos'] }` - matches all queries starting with 'todos'

### Query Functions

Query functions must return a promise that resolves data or throws an error:

```tsx
// Using fetch
queryFn: async () => {
  const res = await fetch(url);
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

// Using axios
queryFn: () => axios.get(url).then(res => res.data)

// With query key access
queryFn: ({ queryKey }) => {
  const [_, todoId] = queryKey;
  return fetchTodo(todoId);
}
```

### Important Defaults

Understanding defaults is crucial for optimal usage:

- **staleTime: 0** - Queries become stale immediately by default
- **gcTime: 5 minutes** - Unused/inactive cache data remains in memory for 5 minutes
- **retry: 3** - Failed queries retry 3 times with exponential backoff
- **refetchOnWindowFocus: true** - Queries refetch when window regains focus
- **refetchOnReconnect: true** - Queries refetch when network reconnects

```tsx
// Override defaults globally
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      gcTime: 1000 * 60 * 10, // 10 minutes
    },
  },
});

// Or per query
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: 1000 * 60, // 1 minute
  retry: 5,
});
```

### Query Status and Fetch Status

Queries have two important states:

**Query Status:**
- `pending` - No cached data, query is executing
- `error` - Query encountered an error
- `success` - Query succeeded and data is available

**Fetch Status:**
- `fetching` - Query function is executing
- `paused` - Query wants to fetch but is paused (offline)
- `idle` - Query is not fetching

```tsx
const { data, status, fetchStatus, isLoading, isFetching } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
});

// isLoading = status === 'pending'
// isFetching = fetchStatus === 'fetching'
```

### Query Invalidation

Mark queries as stale to trigger refetches:

```tsx
const queryClient = useQueryClient();

// Invalidate all todos queries
queryClient.invalidateQueries({ queryKey: ['todos'] });

// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['todo', todoId] });

// Invalidate and refetch immediately
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'active' // only refetch active queries
});
```

### Mutations

Mutations are used for creating, updating, or deleting data:

```tsx
const mutation = useMutation({
  mutationFn: (newTodo) => {
    return fetch('/api/todos', {
      method: 'POST',
      body: JSON.stringify(newTodo),
    });
  },
  onSuccess: (data, variables, context) => {
    console.log('Success!', data);
  },
  onError: (error, variables, context) => {
    console.error('Error:', error);
  },
  onSettled: (data, error, variables, context) => {
    console.log('Mutation finished');
  },
});

// Trigger mutation
mutation.mutate({ title: 'New Todo' });

// With async/await
mutation.mutateAsync({ title: 'New Todo' })
  .then(data => console.log(data))
  .catch(error => console.error(error));
```

### React Suspense Integration

TanStack Query supports React Suspense with dedicated hooks:

```tsx
import { useSuspenseQuery } from '@tanstack/react-query';

function TodoList() {
  // This will suspend the component until data is ready
  const { data } = useSuspenseQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });

  // No need for loading states - handled by Suspense boundary
  return (
    <ul>
      {data.map((todo) => (
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  );
}

// In parent component
function App() {
  return (
    <Suspense fallback={<div>Loading todos...</div>}>
      <TodoList />
    </Suspense>
  );
}
```

### Streamed Queries (Experimental)

Consume `AsyncIterable` streams as query data - ideal for AI chat, SSE, and streaming responses:

```tsx
import { useQuery, queryOptions } from '@tanstack/react-query';
import { experimental_streamedQuery as streamedQuery } from '@tanstack/react-query';

async function* fetchChatStream(sessionId: string): AsyncIterable<string> {
  const response = await fetch(`/api/chat/${sessionId}`, { method: 'POST' });
  const reader = response.body!.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    yield decoder.decode(value);
  }
}

function ChatMessages({ sessionId }: { sessionId: string }) {
  const { data: chunks, status, fetchStatus } = useQuery(
    queryOptions({
      queryKey: ['chat', sessionId],
      queryFn: streamedQuery({
        streamFn: () => fetchChatStream(sessionId),
        // Optional: customize how chunks accumulate
        // reducer: (acc, chunk) => [...acc, chunk],
        // initialValue: [],
        refetchMode: 'reset',  // 'reset' | 'append' | 'replace'
      }),
    })
  );

  // status === 'pending' until first chunk arrives
  // status === 'success' after first chunk, fetchStatus === 'fetching' until stream ends
  if (status === 'pending') return <div>Waiting for response...</div>;

  return (
    <div>
      {chunks?.map((chunk, i) => <span key={i}>{chunk}</span>)}
      {fetchStatus === 'fetching' && <span className="cursor" />}
    </div>
  );
}
```

**`refetchMode` options:**
- `'reset'` - clear data and start fresh on refetch
- `'append'` - keep existing chunks and add new ones
- `'replace'` - replace data chunk-by-chunk on refetch

**Note:** The API stabilized at v5.86.0. Earlier versions used `queryFn` instead of `streamFn` and `maxChunks` instead of `reducer`.

### Prefetch in Render (Experimental)

Use React 19's `React.use()` with TanStack Query for "render-as-you-fetch":

```tsx
// Enable the feature flag
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      experimental_prefetchInRender: true,
    },
  },
});

// Component that suspends with React.use()
function TodoList({ query }: { query: UseQueryResult<Todo[]> }) {
  const data = React.use(query.promise); // Suspends until resolved
  return <ul>{data.map(todo => <li key={todo.id}>{todo.title}</li>)}</ul>;
}

function App() {
  const query = useQuery({ queryKey: ['todos'], queryFn: fetchTodos });
  return (
    <React.Suspense fallback={<div>Loading...</div>}>
      <TodoList query={query} />
    </React.Suspense>
  );
}
```

**Known limitations:** queries may run twice on unsuspend, incompatible with `useQueries`, `skipToken` and `refetch()` cannot be used together.

## Advanced Topics

For detailed information on advanced patterns, see the reference files:

### Infinite Queries

For implementing infinite scroll and load-more patterns:
- See `infinite-queries.md` for comprehensive guide
- Covers `useInfiniteQuery` hook
- Bidirectional pagination
- `getNextPageParam` and `getPreviousPageParam`
- Refetching and background updates

### Optimistic Updates

For updating UI before server confirmation:
- See `optimistic-updates.md` for detailed patterns
- Optimistic mutations
- Rollback on error
- Context for cancellation
- UI feedback strategies

### TypeScript Support

For full type safety and inference:
- See `query-typescript.md` for complete TypeScript guide
- Type inference from query functions
- Generic type parameters
- Typing query options
- Custom hooks with types
- Error type narrowing

### Query Invalidation Patterns

For advanced cache invalidation strategies:
- See `query-invalidation.md`
- Partial matching
- Predicate functions
- Refetch strategies
- Query filters

### Performance Optimization

For optimizing query performance:
- See `query-performance.md`
- Query deduplication
- Structural sharing
- Memory management
- Query splitting strategies

## DevTools

TanStack Query DevTools provide visual insights into query state:

```bash
npm install @tanstack/react-query-devtools
```

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
}
```

**DevTools features:**
- View all queries and their states
- Inspect query data and errors
- Manually trigger refetches
- Invalidate queries
- Monitor cache lifecycle
- Visual indicator for `staleTime: Infinity` ("static") queries (v5.80.0+)

## Common Patterns

### Dependent Queries

Run queries in sequence when one depends on another:

```tsx
// First query
const { data: user } = useQuery({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
});

// Second query depends on first
const { data: projects } = useQuery({
  queryKey: ['projects', user?.id],
  queryFn: () => fetchProjects(user.id),
  enabled: !!user?.id, // Only run when user.id is available
});
```

### Parallel Queries

Multiple independent queries in one component:

```tsx
function Dashboard() {
  const users = useQuery({ queryKey: ['users'], queryFn: fetchUsers });
  const posts = useQuery({ queryKey: ['posts'], queryFn: fetchPosts });
  const stats = useQuery({ queryKey: ['stats'], queryFn: fetchStats });

  if (users.isLoading || posts.isLoading || stats.isLoading) {
    return <div>Loading...</div>;
  }

  // All queries succeeded
  return <DashboardView users={users.data} posts={posts.data} stats={stats.data} />;
}
```

### Dynamic Parallel Queries

Use `useQueries` for dynamic number of queries:

```tsx
import { useQueries } from '@tanstack/react-query';

function TodoLists({ listIds }) {
  const results = useQueries({
    queries: listIds.map((id) => ({
      queryKey: ['list', id],
      queryFn: () => fetchList(id),
    })),
  });

  const isLoading = results.some(result => result.isLoading);
  const data = results.map(result => result.data);

  return <Lists data={data} />;
}
```

### Prefetching

Prefetch data before it's needed:

```tsx
const queryClient = useQueryClient();

// Prefetch on hover
function TodoListLink({ id }) {
  const prefetch = () => {
    queryClient.prefetchQuery({
      queryKey: ['todo', id],
      queryFn: () => fetchTodo(id),
      staleTime: 1000 * 60 * 5, // Cache for 5 minutes
    });
  };

  return (
    <Link to={`/todo/${id}`} onMouseEnter={prefetch}>
      View Todo
    </Link>
  );
}
```

### Initial Data

Provide initial data to avoid loading states:

```tsx
function TodoDetail({ todoId, initialTodo }) {
  const { data } = useQuery({
    queryKey: ['todo', todoId],
    queryFn: () => fetchTodo(todoId),
    initialData: initialTodo, // Use this data immediately
    staleTime: 1000 * 60, // Consider fresh for 1 minute
  });

  return <div>{data.title}</div>;
}
```

### Placeholder Data

Show placeholder while loading:

```tsx
const { data, isPlaceholderData } = useQuery({
  queryKey: ['todos', page],
  queryFn: () => fetchTodos(page),
  placeholderData: (previousData) => previousData, // Keep previous data while loading
});

// Or use static placeholder
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  placeholderData: { items: [], total: 0 },
});

// TypeScript: isPlaceholderData now narrows data type (v5.65.0+)
// When isPlaceholderData is true, data is typed as the placeholder type
```

### tRPC v11 Integration

tRPC v11 exposes `queryOptions` and `mutationOptions` directly, removing the need for custom hook wrappers:

```tsx
import { useTRPC } from '@trpc/tanstack-react-query';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function TodoList() {
  const trpc = useTRPC();
  const queryClient = useQueryClient();

  // Direct queryOptions pattern (replaces trpc.todo.list.useQuery())
  const { data } = useQuery(trpc.todo.list.queryOptions());

  const createTodo = useMutation(
    trpc.todo.create.mutationOptions({
      onSuccess: () => {
        queryClient.invalidateQueries(trpc.todo.list.queryOptions());
      },
    })
  );

  // Prefetching also works
  queryClient.prefetchQuery(trpc.todo.list.queryOptions());
}
```

Requires `@tanstack/react-query@5.62.8+` and `@trpc/tanstack-react-query`.

## Error Handling

### Query Errors

```tsx
const { error, isError } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
});

if (isError) {
  return <div>Error: {error.message}</div>;
}
```

### Global Error Handling

Use `QueryCache` and `MutationCache` callbacks for global error handling:

```tsx
import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      console.error(`Query ${query.queryKey} failed:`, error);
      // Show toast notification, etc.
    },
  }),
  mutationCache: new MutationCache({
    onError: (error, _variables, _context, mutation) => {
      console.error('Mutation failed:', error);
    },
  }),
});
```

### Error Boundaries

Combine with React Error Boundaries:

```tsx
import { useQuery } from '@tanstack/react-query';
import { ErrorBoundary } from 'react-error-boundary';

function TodoList() {
  const { data } = useQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
    throwOnError: true, // Throw errors to error boundary
  });

  return <div>{/* render data */}</div>;
}

function App() {
  return (
    <ErrorBoundary fallback={<div>Something went wrong</div>}>
      <TodoList />
    </ErrorBoundary>
  );
}
```

## Best Practices

1. **Use Query Keys Wisely**
   - Structure keys hierarchically: `['todos', 'list', { filters }]`
   - Include all variables in the key
   - Keep keys consistent across your app

2. **Set Appropriate staleTime**
   - Static data: `staleTime: Infinity`
   - Frequently changing: `staleTime: 0` (default)
   - Moderately changing: `staleTime: 1000 * 60 * 5` (5 minutes)

3. **Handle Loading and Error States**
   - Always check `isLoading` and `error`
   - Provide meaningful loading indicators
   - Show user-friendly error messages

4. **Optimize Refetching**
   - Disable unnecessary refetches with `refetchOnWindowFocus: false`
   - Use `staleTime` to reduce refetches
   - Consider using `refetchInterval` for polling

5. **Invalidate Efficiently**
   - Invalidate specific queries, not all queries
   - Use query key prefixes for related queries
   - Combine with optimistic updates for better UX

6. **Use TypeScript**
   - Type your query functions for type inference
   - Use generic type parameters when needed
   - Enable strict type checking

7. **Leverage DevTools**
   - Install DevTools in development
   - Monitor query behavior
   - Debug cache issues

## Resources

- **Official Documentation**: https://tanstack.com/query/latest/docs/framework/react/overview
- **GitHub Repository**: https://github.com/TanStack/query
- **Examples**: https://tanstack.com/query/latest/docs/framework/react/examples
- **Community**: https://discord.gg/tanstack
- **TypeScript Guide**: https://tanstack.com/query/latest/docs/framework/react/typescript

## Migration from v4

If you're upgrading from React Query v4:

- `cacheTime` renamed to `gcTime`
- `useInfiniteQuery` pageParam changes
- New `useSuspenseQuery` hooks
- Improved TypeScript inference
- v4.42.0 added React 19 support for teams not yet migrated to v5
- See official migration guide: https://tanstack.com/query/latest/docs/framework/react/guides/migrating-to-v5
