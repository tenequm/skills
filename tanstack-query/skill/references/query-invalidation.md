# Query Invalidation

Query invalidation is the process of marking queries as stale and potentially refetching them. This is essential for keeping your cache in sync with server state after mutations.

## Basic Invalidation

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function CreateTodo() {
  const queryClient = useQueryClient();

  const mutation = useMutation({
    mutationFn: (newTodo) => {
      return fetch('/api/todos', {
        method: 'POST',
        body: JSON.stringify(newTodo),
      }).then(res => res.json());
    },
    onSuccess: () => {
      // Mark todos queries as stale and refetch
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  return (
    <button onClick={() => mutation.mutate({ title: 'New Todo' })}>
      Create Todo
    </button>
  );
}
```

## Invalidation Methods

### invalidateQueries

Marks queries as stale and triggers refetch of active queries:

```tsx
// Invalidate all queries
queryClient.invalidateQueries();

// Invalidate specific query
queryClient.invalidateQueries({ queryKey: ['todos'] });

// Invalidate query with exact match
queryClient.invalidateQueries({ queryKey: ['todo', todoId], exact: true });

// Invalidate and wait for refetch
await queryClient.invalidateQueries({ queryKey: ['todos'] });
```

### refetchQueries

Directly refetch queries without marking as stale first:

```tsx
// Refetch all queries
queryClient.refetchQueries();

// Refetch specific queries
queryClient.refetchQueries({ queryKey: ['todos'] });

// Refetch only active queries
queryClient.refetchQueries({ queryKey: ['todos'], type: 'active' });

// Refetch only inactive queries
queryClient.refetchQueries({ queryKey: ['todos'], type: 'inactive' });
```

### resetQueries

Reset queries to their initial state:

```tsx
// Reset and refetch
queryClient.resetQueries({ queryKey: ['todos'] });

// Reset specific query
queryClient.resetQueries({ queryKey: ['todo', todoId] });
```

## Query Key Matching

### Prefix Matching

By default, invalidateQueries uses prefix matching:

```tsx
// This query
useQuery({ queryKey: ['todos', 'list', { page: 1 }], queryFn: fetchTodos });

// Is invalidated by any of these:
queryClient.invalidateQueries({ queryKey: ['todos'] });
queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
queryClient.invalidateQueries({ queryKey: ['todos', 'list', { page: 1 }] });

// But NOT by these:
queryClient.invalidateQueries({ queryKey: ['todos', 'detail'] });
queryClient.invalidateQueries({ queryKey: ['users'] });
```

### Exact Matching

Use `exact: true` for precise matching:

```tsx
// Only invalidate this exact query key
queryClient.invalidateQueries({
  queryKey: ['todos', 'list', { page: 1 }],
  exact: true,
});

// This would invalidate:
useQuery({ queryKey: ['todos', 'list', { page: 1 }], ... });

// But NOT these:
useQuery({ queryKey: ['todos', 'list', { page: 2 }], ... });
useQuery({ queryKey: ['todos', 'list'], ... });
useQuery({ queryKey: ['todos'], ... });
```

### Predicate Functions

Use custom matching logic:

```tsx
// Invalidate all todos queries except detail queries
queryClient.invalidateQueries({
  predicate: (query) => {
    return query.queryKey[0] === 'todos' && query.queryKey[1] !== 'detail';
  },
});

// Invalidate stale queries only
queryClient.invalidateQueries({
  predicate: (query) => {
    return query.state.isInvalidated;
  },
});

// Invalidate based on query data
queryClient.invalidateQueries({
  predicate: (query) => {
    const data = query.state.data as Todo[] | undefined;
    return data?.some((todo) => todo.userId === targetUserId) ?? false;
  },
});
```

## Invalidation Timing

### Immediate Invalidation

Invalidate and refetch immediately:

```tsx
const mutation = useMutation({
  mutationFn: createTodo,
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

### Delayed Invalidation

Wait for mutation to settle:

```tsx
const mutation = useMutation({
  mutationFn: createTodo,
  onSettled: () => {
    // Runs after success or error
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

### Conditional Invalidation

Only invalidate under certain conditions:

```tsx
const mutation = useMutation({
  mutationFn: updateTodo,
  onSuccess: (data, variables) => {
    if (data.isPublished) {
      // Only invalidate if todo was published
      queryClient.invalidateQueries({ queryKey: ['todos', 'published'] });
    }
  },
});
```

## Refetch Strategies

### Refetch Active Queries Only

```tsx
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'active', // Only refetch active queries (default)
});
```

### Refetch All Queries

```tsx
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'all', // Refetch both active and inactive queries
});
```

### Don't Refetch

```tsx
queryClient.invalidateQueries({
  queryKey: ['todos'],
  refetchType: 'none', // Only mark as stale, don't refetch
});
```

## Invalidation Patterns

### After Create

```tsx
const createTodo = useMutation({
  mutationFn: (newTodo) => fetch('/api/todos', { method: 'POST', ... }),
  onSuccess: () => {
    // Invalidate list queries to show new item
    queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
  },
});
```

### After Update

```tsx
const updateTodo = useMutation({
  mutationFn: ({ id, updates }) => fetch(`/api/todos/${id}`, { method: 'PATCH', ... }),
  onSuccess: (data, { id }) => {
    // Invalidate specific item
    queryClient.invalidateQueries({ queryKey: ['todo', id] });
    // Invalidate list in case item moved categories, etc.
    queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
  },
});
```

### After Delete

```tsx
const deleteTodo = useMutation({
  mutationFn: (id) => fetch(`/api/todos/${id}`, { method: 'DELETE' }),
  onSuccess: (_, id) => {
    // Remove specific item from cache
    queryClient.removeQueries({ queryKey: ['todo', id] });
    // Invalidate lists
    queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
  },
});
```

### Bulk Operations

```tsx
const markAllDone = useMutation({
  mutationFn: () => fetch('/api/todos/mark-all-done', { method: 'POST' }),
  onSuccess: () => {
    // Invalidate all todo-related queries
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

## Related Query Invalidation

### Update Multiple Related Queries

```tsx
const updateUser = useMutation({
  mutationFn: ({ userId, updates }) => updateUserApi(userId, updates),
  onSuccess: (data, { userId }) => {
    // Invalidate user detail
    queryClient.invalidateQueries({ queryKey: ['user', userId] });
    // Invalidate user list
    queryClient.invalidateQueries({ queryKey: ['users'] });
    // Invalidate user's posts
    queryClient.invalidateQueries({ queryKey: ['posts', 'user', userId] });
    // Invalidate user's comments
    queryClient.invalidateQueries({ queryKey: ['comments', 'user', userId] });
  },
});
```

### Hierarchical Invalidation

```tsx
// Query key structure:
// ['todos'] - all todos
// ['todos', 'list'] - todo lists
// ['todos', 'list', filters] - filtered lists
// ['todos', 'detail'] - todo details
// ['todos', 'detail', id] - specific todo

const updateTodo = useMutation({
  mutationFn: updateTodoApi,
  onSuccess: (data, { id }) => {
    // Invalidate specific todo detail
    queryClient.invalidateQueries({ queryKey: ['todos', 'detail', id] });
    // Invalidate all list queries (they might show this todo)
    queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
  },
});
```

## Invalidation with Infinite Queries

### Invalidate All Pages

```tsx
const createPost = useMutation({
  mutationFn: (newPost) => createPostApi(newPost),
  onSuccess: () => {
    // Refetches all pages
    queryClient.invalidateQueries({ queryKey: ['posts'] });
  },
});
```

### Invalidate Specific Pages

```tsx
queryClient.invalidateQueries({
  queryKey: ['posts'],
  refetchPage: (page, index) => {
    // Only refetch first page
    return index === 0;
  },
});
```

### Selective Page Refetch

```tsx
const updatePost = useMutation({
  mutationFn: ({ id, updates }) => updatePostApi(id, updates),
  onSuccess: (data, { id }) => {
    queryClient.invalidateQueries({
      queryKey: ['posts'],
      refetchPage: (page, index) => {
        // Only refetch pages containing this post
        return page.posts.some((post) => post.id === id);
      },
    });
  },
});
```

## Advanced Invalidation

### Cascading Invalidation

```tsx
const deleteProject = useMutation({
  mutationFn: (projectId) => deleteProjectApi(projectId),
  onSuccess: async (_, projectId) => {
    // Step 1: Remove project from cache
    queryClient.removeQueries({ queryKey: ['project', projectId] });

    // Step 2: Invalidate project list
    await queryClient.invalidateQueries({ queryKey: ['projects'] });

    // Step 3: Invalidate related resources
    await queryClient.invalidateQueries({ queryKey: ['tasks', 'project', projectId] });
    await queryClient.invalidateQueries({ queryKey: ['members', 'project', projectId] });

    // Step 4: Invalidate summary/stats
    await queryClient.invalidateQueries({ queryKey: ['stats'] });
  },
});
```

### Debounced Invalidation

For frequent updates, debounce invalidation:

```tsx
import { useDebouncedCallback } from 'use-debounce';

function SearchableList() {
  const queryClient = useQueryClient();

  const debouncedInvalidate = useDebouncedCallback(() => {
    queryClient.invalidateQueries({ queryKey: ['search-results'] });
  }, 500);

  const updateFilters = (newFilters) => {
    setFilters(newFilters);
    debouncedInvalidate();
  };

  return <FilterPanel onChange={updateFilters} />;
}
```

### Throttled Invalidation

```tsx
import { throttle } from 'lodash';

const throttledInvalidate = throttle(() => {
  queryClient.invalidateQueries({ queryKey: ['live-data'] });
}, 1000);

// In a websocket listener
socket.on('update', () => {
  throttledInvalidate();
});
```

## Query Filters

Use query filters for more complex matching. v5.90.8+ supports partial query keys and preserves `readonly` from `as const` assertions:

```tsx
import { QueryFilters } from '@tanstack/react-query';

const filters: QueryFilters = {
  queryKey: ['todos'],
  type: 'active',        // 'active' | 'inactive' | 'all'
  stale: true,           // Only stale queries
  exact: false,          // Prefix matching (supports partial keys)
  predicate: (query) => {
    // Custom logic
    return query.state.dataUpdatedAt > Date.now() - 60000;
  },
};

queryClient.invalidateQueries(filters);

// Partial key matching with as const (v5.90.8+)
const todoKeys = { all: ['todos'] as const };
queryClient.invalidateQueries({ queryKey: todoKeys.all }); // readonly works
```

### Filter by State

```tsx
// Only invalidate stale queries
queryClient.invalidateQueries({
  queryKey: ['todos'],
  stale: true,
});

// Only invalidate fetching queries
queryClient.invalidateQueries({
  predicate: (query) => query.state.fetchStatus === 'fetching',
});
```

### Filter by Type

```tsx
// Only active queries (currently mounted)
queryClient.invalidateQueries({
  queryKey: ['todos'],
  type: 'active',
});

// Only inactive queries (not mounted)
queryClient.invalidateQueries({
  queryKey: ['todos'],
  type: 'inactive',
});

// All queries
queryClient.invalidateQueries({
  queryKey: ['todos'],
  type: 'all',
});
```

## Performance Considerations

### Batch Invalidations

```tsx
// ❌ Multiple separate invalidations
queryClient.invalidateQueries({ queryKey: ['todos'] });
queryClient.invalidateQueries({ queryKey: ['users'] });
queryClient.invalidateQueries({ queryKey: ['projects'] });

// ✅ Batch with predicate
queryClient.invalidateQueries({
  predicate: (query) => {
    const key = query.queryKey[0];
    return key === 'todos' || key === 'users' || key === 'projects';
  },
});
```

### Smart Invalidation

Only invalidate what's needed:

```tsx
const updateTodo = useMutation({
  mutationFn: updateTodoApi,
  onSuccess: (data, { id, updates }) => {
    // If only title changed, no need to invalidate lists
    if (Object.keys(updates).length === 1 && 'title' in updates) {
      queryClient.invalidateQueries({ queryKey: ['todo', id], exact: true });
    } else {
      // Status/category changed, invalidate lists too
      queryClient.invalidateQueries({ queryKey: ['todo', id] });
      queryClient.invalidateQueries({ queryKey: ['todos', 'list'] });
    }
  },
});
```

### Prevent Over-Invalidation

```tsx
// ❌ Too broad - invalidates everything
queryClient.invalidateQueries();

// ❌ Still too broad - invalidates all todo queries
queryClient.invalidateQueries({ queryKey: ['todos'] });

// ✅ Specific - only invalidates affected queries
queryClient.invalidateQueries({ queryKey: ['todos', 'list', filters] });
queryClient.invalidateQueries({ queryKey: ['todo', todoId] });
```

## Alternatives to Invalidation

Sometimes you don't need invalidation:

### Direct Cache Update

```tsx
const toggleTodo = useMutation({
  mutationFn: (todoId) => toggleTodoApi(todoId),
  onSuccess: (data, todoId) => {
    // Directly update cache instead of invalidating
    queryClient.setQueryData(['todo', todoId], data);
    queryClient.setQueryData(['todos'], (old) =>
      old?.map((todo) => (todo.id === todoId ? data : todo))
    );
  },
});
```

### Optimistic Updates

```tsx
const updateTodo = useMutation({
  mutationFn: updateTodoApi,
  onMutate: async ({ id, updates }) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previous = queryClient.getQueryData(['todos']);

    // Update cache optimistically
    queryClient.setQueryData(['todos'], (old) =>
      old?.map((todo) => (todo.id === id ? { ...todo, ...updates } : todo))
    );

    return { previous };
  },
  onError: (err, vars, context) => {
    queryClient.setQueryData(['todos'], context.previous);
  },
  // No need for invalidation if optimistic update is accurate
});
```

### Polling

```tsx
// Instead of manual invalidation, use automatic refetching
useQuery({
  queryKey: ['live-data'],
  queryFn: fetchLiveData,
  refetchInterval: 5000, // Auto-refetch every 5 seconds
});
```

### Known Issues (Fixed)

These bugs can manifest as invalidation-related surprises. They're fixed in latest versions but worth knowing:

- **`combine` stable reference bug (fixed v5.90.19):** When passing a stable (non-inline) `combine` function to `useQueries`, it was not called with correct parameters when queries changed dynamically. Workaround: pass `combine` inline until fix is applied.
- **`useSuspenseQueries` duplicate keys (fixed v5.90.11):** Passing duplicate `queryKeys` to `useSuspenseQueries` caused infinite render loops instead of an error.
- **SSR dehydration (fixed v5.90.3):** Unhandled promise rejections during de/rehydration of pending queries.

## Best Practices

1. **Be Specific with Query Keys**
   ```tsx
   // ✅ Good - specific invalidation
   queryClient.invalidateQueries({ queryKey: ['todos', 'list', filters] });

   // ❌ Bad - too broad
   queryClient.invalidateQueries({ queryKey: ['todos'] });
   ```

2. **Use Exact Matching When Appropriate**
   ```tsx
   queryClient.invalidateQueries({
     queryKey: ['todo', todoId],
     exact: true, // Only this specific todo
   });
   ```

3. **Invalidate in onSuccess for Success-Only**
   ```tsx
   onSuccess: () => {
     queryClient.invalidateQueries({ queryKey: ['todos'] });
   }
   ```

4. **Invalidate in onSettled for Always**
   ```tsx
   onSettled: () => {
     queryClient.invalidateQueries({ queryKey: ['todos'] });
   }
   ```

5. **Consider Alternatives**
   - Direct cache updates for simple changes
   - Optimistic updates for better UX
   - Polling for real-time data

6. **Batch Related Invalidations**
   ```tsx
   await Promise.all([
     queryClient.invalidateQueries({ queryKey: ['todos'] }),
     queryClient.invalidateQueries({ queryKey: ['stats'] }),
   ]);
   ```

7. **Use Predicate Functions for Complex Logic**
   ```tsx
   queryClient.invalidateQueries({
     predicate: (query) => {
       // Custom matching logic
       return shouldInvalidate(query);
     },
   });
   ```

8. **Monitor Invalidation Performance**
   - Use React Query DevTools
   - Check for unnecessary refetches
   - Optimize query key structure
