# Performance Optimization

Optimize TanStack Query for better performance, reduced network requests, and improved user experience.

## Query Configuration

### staleTime

Control how long data is considered fresh:

```tsx
// ❌ Default - data stale immediately
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: 0, // default
});

// ✅ Optimized - data fresh for 5 minutes
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  staleTime: 1000 * 60 * 5, // 5 minutes
});

// ✅ Static data - never stale
useQuery({
  queryKey: ['config'],
  queryFn: fetchConfig,
  staleTime: Infinity,
});
```

### gcTime (formerly cacheTime)

Control how long unused data stays in cache:

```tsx
// Default - 5 minutes
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  gcTime: 1000 * 60 * 5, // default
});

// Extended cache for frequently accessed data
useQuery({
  queryKey: ['user-profile'],
  queryFn: fetchUserProfile,
  gcTime: 1000 * 60 * 30, // 30 minutes
});

// Immediate cleanup for sensitive data
useQuery({
  queryKey: ['payment-info'],
  queryFn: fetchPaymentInfo,
  gcTime: 0, // Remove immediately when unused
});
```

### Disable Unnecessary Refetching

```tsx
// Disable all automatic refetching
useQuery({
  queryKey: ['static-data'],
  queryFn: fetchStaticData,
  refetchOnWindowFocus: false,
  refetchOnReconnect: false,
  refetchOnMount: false,
});

// Global defaults
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    },
  },
});
```

## Query Deduplication

TanStack Query automatically deduplicates identical requests:

```tsx
// These three components all request the same data
function Component1() {
  useQuery({ queryKey: ['user', userId], queryFn: fetchUser });
}

function Component2() {
  useQuery({ queryKey: ['user', userId], queryFn: fetchUser });
}

function Component3() {
  useQuery({ queryKey: ['user', userId], queryFn: fetchUser });
}

// Result: Only ONE network request is made
// All three components share the same cached data
```

## Structural Sharing

TanStack Query preserves referential equality when data hasn't changed:

```tsx
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  // Structural sharing is enabled by default
  structuralSharing: true,
});

// If server returns identical data, React won't re-render
// because data reference hasn't changed
```

Disable for very large datasets:

```tsx
useQuery({
  queryKey: ['large-dataset'],
  queryFn: fetchLargeDataset,
  structuralSharing: false, // Skip structural sharing for performance
});
```

**Note:** v5.85.7 improved the internal `replaceEqualDeep` function to use `Set` for O(1) lookups instead of `Array.indexOf`, improving performance for queries returning large arrays.

## Prefetching

Load data before it's needed:

### Hover Prefetch

```tsx
const queryClient = useQueryClient();

function TodoListItem({ todo }) {
  const prefetchTodo = () => {
    queryClient.prefetchQuery({
      queryKey: ['todo', todo.id],
      queryFn: () => fetchTodo(todo.id),
      staleTime: 1000 * 60 * 5,
    });
  };

  return (
    <Link
      to={`/todo/${todo.id}`}
      onMouseEnter={prefetchTodo}
      onFocus={prefetchTodo}
    >
      {todo.title}
    </Link>
  );
}
```

### Route-Based Prefetch

```tsx
// In router loader or component
async function todoLoader({ params }) {
  await queryClient.prefetchQuery({
    queryKey: ['todo', params.id],
    queryFn: () => fetchTodo(params.id),
  });
}

// Or in a parent component
function TodoLayout() {
  const navigate = useNavigate();

  useEffect(() => {
    // Prefetch common routes
    queryClient.prefetchQuery({
      queryKey: ['todos'],
      queryFn: fetchTodos,
    });
  }, []);

  return <Outlet />;
}
```

### Predictive Prefetch

```tsx
function PaginatedList({ page }) {
  const { data } = useQuery({
    queryKey: ['items', page],
    queryFn: () => fetchItems(page),
  });

  // Prefetch next page
  useEffect(() => {
    if (page < totalPages) {
      queryClient.prefetchQuery({
        queryKey: ['items', page + 1],
        queryFn: () => fetchItems(page + 1),
      });
    }
  }, [page]);

  return <div>{/* render items */}</div>;
}
```

## Data Transformation

### Use select for Transformation

```tsx
// ❌ Transform in component - runs on every render
function TodoList() {
  const { data } = useQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });

  const completedTodos = data?.filter(todo => todo.completed);
  return <div>{completedTodos?.map(/* ... */)}</div>;
}

// ✅ Transform with select - memoized automatically
function TodoList() {
  const { data: completedTodos } = useQuery({
    queryKey: ['todos'],
    queryFn: fetchTodos,
    select: (todos) => todos.filter(todo => todo.completed),
  });

  return <div>{completedTodos?.map(/* ... */)}</div>;
}
```

### Select is Memoized

```tsx
// select function only runs when data changes
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  select: (todos) => {
    console.log('Transforming...'); // Only logs when data changes
    return todos.map(todo => ({
      ...todo,
      displayName: `${todo.id}: ${todo.title}`,
    }));
  },
});
```

## Pagination Optimization

### Offset Pagination

```tsx
function PaginatedTodos() {
  const [page, setPage] = useState(1);

  const { data } = useQuery({
    queryKey: ['todos', page],
    queryFn: () => fetchTodos(page),
    staleTime: 1000 * 60 * 5, // Keep pages fresh
    placeholderData: (previousData) => previousData, // Keep previous data while loading
  });

  return (
    <div>
      {data?.items.map(todo => <TodoItem key={todo.id} todo={todo} />)}
      <button onClick={() => setPage(p => p - 1)} disabled={page === 1}>
        Previous
      </button>
      <button onClick={() => setPage(p => p + 1)}>
        Next
      </button>
    </div>
  );
}
```

### Infinite Queries with Windowing

For very long lists, use virtual scrolling:

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';
import { useVirtualizer } from '@tanstack/react-virtual';

function VirtualizedInfiniteList() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ['items'],
    queryFn: ({ pageParam = 0 }) => fetchItems(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  const allItems = data?.pages.flatMap(page => page.items) ?? [];
  const parentRef = useRef(null);

  const virtualizer = useVirtualizer({
    count: hasNextPage ? allItems.length + 1 : allItems.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 100,
  });

  useEffect(() => {
    const lastItem = virtualizer.getVirtualItems()[virtualizer.getVirtualItems().length - 1];

    if (!lastItem) return;

    if (lastItem.index >= allItems.length - 1 && hasNextPage) {
      fetchNextPage();
    }
  }, [hasNextPage, fetchNextPage, allItems.length, virtualizer.getVirtualItems()]);

  return (
    <div ref={parentRef} style={{ height: '500px', overflow: 'auto' }}>
      <div style={{ height: `${virtualizer.getTotalSize()}px` }}>
        {virtualizer.getVirtualItems().map((virtualRow) => (
          <div
            key={virtualRow.index}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualRow.size}px`,
              transform: `translateY(${virtualRow.start}px)`,
            }}
          >
            {allItems[virtualRow.index] ? (
              <Item item={allItems[virtualRow.index]} />
            ) : (
              'Loading...'
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
```

## Parallel Queries Optimization

### Using useQueries

```tsx
// ❌ Sequential queries
async function fetchAllData() {
  const users = await fetchUsers();
  const posts = await fetchPosts();
  const comments = await fetchComments();
  return { users, posts, comments };
}

// ✅ Parallel queries
function Dashboard() {
  const results = useQueries({
    queries: [
      { queryKey: ['users'], queryFn: fetchUsers },
      { queryKey: ['posts'], queryFn: fetchPosts },
      { queryKey: ['comments'], queryFn: fetchComments },
    ],
  });

  const [users, posts, comments] = results;
  const isLoading = results.some(r => r.isLoading);

  return <div>{/* render */}</div>;
}
```

### Dynamic Parallel Queries

```tsx
function UserPosts({ userIds }) {
  const queries = useQueries({
    queries: userIds.map(id => ({
      queryKey: ['user-posts', id],
      queryFn: () => fetchUserPosts(id),
      staleTime: 1000 * 60 * 5,
    })),
  });

  return <div>{/* render */}</div>;
}
```

## Memory Management

### Limit Cache Size

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      gcTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

// Manually clear old queries
queryClient.clear(); // Clear all cache

// Remove specific queries
queryClient.removeQueries({ queryKey: ['old-data'] });
```

### Remove Queries on Unmount

```tsx
function ExpensiveComponent() {
  const { data } = useQuery({
    queryKey: ['expensive-data'],
    queryFn: fetchExpensiveData,
    gcTime: 0, // Remove immediately when component unmounts
  });

  return <div>{/* render */}</div>;
}
```

## Network Optimization

### Batch Requests

If your API supports batching:

```tsx
// Collect query keys and batch them
const batchedQueryFn = async (keys) => {
  const ids = keys.map(key => key[1]);
  const results = await fetch(`/api/items?ids=${ids.join(',')}`);
  return results.json();
};

// Use in queries
useQuery({
  queryKey: ['item', itemId],
  queryFn: () => batchedQueryFn([['item', itemId]]),
});
```

### Request Cancellation

```tsx
useQuery({
  queryKey: ['search', searchTerm],
  queryFn: async ({ signal }) => {
    // AbortSignal automatically provided
    const res = await fetch(`/api/search?q=${searchTerm}`, { signal });
    return res.json();
  },
});

// When searchTerm changes, previous request is cancelled
```

### Retry Configuration

```tsx
// ❌ Retry immediately 3 times
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  retry: 3,
});

// ✅ Exponential backoff
useQuery({
  queryKey: ['todos'],
  queryFn: fetchTodos,
  retry: 3,
  retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
});
```

## Dependent Queries

Avoid waterfalls by enabling queries in parallel when possible:

```tsx
// ❌ Waterfall - queries run sequentially
function UserDashboard({ userId }) {
  const { data: user } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  const { data: posts } = useQuery({
    queryKey: ['posts', user?.id],
    queryFn: () => fetchPosts(user.id),
    enabled: !!user?.id, // Waits for user
  });

  const { data: comments } = useQuery({
    queryKey: ['comments', user?.id],
    queryFn: () => fetchComments(user.id),
    enabled: !!user?.id, // Also waits for user
  });
}

// ✅ Optimized - posts and comments fetch in parallel after user loads
```

## Code Splitting

### Lazy Load Query Client

```tsx
import { lazy, Suspense } from 'react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const ReactQueryDevtools = lazy(() =>
  import('@tanstack/react-query-devtools').then(mod => ({
    default: mod.ReactQueryDevtools,
  }))
);

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <Suspense fallback={null}>
        <ReactQueryDevtools />
      </Suspense>
    </QueryClientProvider>
  );
}
```

## Monitoring Performance

### Using DevTools

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      <ReactQueryDevtools
        initialIsOpen={false}
        position="bottom-right"
      />
    </QueryClientProvider>
  );
}
```

### Query/Mutation Cache Callbacks

Use cache-level callbacks for global logging (the `logger` property was removed in v5):

```tsx
import { QueryClient, QueryCache, MutationCache } from '@tanstack/react-query';

const queryClient = new QueryClient({
  queryCache: new QueryCache({
    onError: (error, query) => {
      console.error(`[Query Error] ${query.queryKey}:`, error);
    },
    onSuccess: (data, query) => {
      console.log(`[Query Success] ${query.queryKey}`);
    },
  }),
  mutationCache: new MutationCache({
    onError: (error) => {
      console.error('[Mutation Error]:', error);
    },
  }),
});
```

DevTools now shows a visual indicator for queries with `staleTime: Infinity` ("static" queries), making it easier to distinguish intentionally never-refetched queries (v5.80.0+).

### timeoutManager (Testing)

Replace `setTimeout`/`setInterval` with custom implementations for testing or non-browser environments (v5.87.0+):

```tsx
import { timeoutManager } from '@tanstack/query-core';

// In test setup - use fake timers
timeoutManager.setTimeout = vi.fn(setTimeout);
timeoutManager.clearTimeout = vi.fn(clearTimeout);
```

### defaultScheduler

The internal notification batching scheduler is now a public export (v5.70.0+), enabling custom scheduling strategies:

```tsx
import { defaultScheduler } from '@tanstack/query-core';
// Use for advanced batching customization
```

### Performance Metrics

```tsx
useQuery({
  queryKey: ['todos'],
  queryFn: async () => {
    const start = performance.now();
    const data = await fetchTodos();
    const duration = performance.now() - start;
    console.log(`Query took ${duration}ms`);
    return data;
  },
});
```

## Best Practices

1. **Set Appropriate staleTime**
   ```tsx
   // Static data
   staleTime: Infinity

   // Frequently changing
   staleTime: 0

   // Moderate
   staleTime: 1000 * 60 * 5 // 5 minutes
   ```

2. **Use Prefetching**
   - Hover intent
   - Route prediction
   - Next page in pagination

3. **Optimize with select**
   ```tsx
   select: (data) => data.filter(/* ... */)
   ```

4. **Disable Unnecessary Refetching**
   ```tsx
   refetchOnWindowFocus: false
   refetchOnReconnect: false
   ```

5. **Use Structural Sharing**
   - Enabled by default
   - Disable for very large datasets

6. **Implement Virtual Scrolling**
   - For long lists
   - For infinite queries

7. **Monitor with DevTools**
   - Watch for unnecessary refetches
   - Check cache effectiveness
   - Identify slow queries

8. **Batch Parallel Queries**
   - Use useQueries
   - Reduce waterfalls

9. **Clean Up Unused Cache**
   ```tsx
   gcTime: 1000 * 60 * 5
   ```

10. **Use Request Cancellation**
    - Automatically handled by TanStack Query
    - Ensures old requests don't override new ones
