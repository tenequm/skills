# Optimistic Updates

Optimistic updates allow you to update the UI immediately before a mutation completes, providing a better user experience. If the mutation fails, you can roll back to the previous state.

## Basic Optimistic Update

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

function TodoList() {
  const queryClient = useQueryClient();

  const toggleTodo = useMutation({
    mutationFn: (todoId) => {
      return fetch(`/api/todos/${todoId}/toggle`, { method: 'POST' });
    },
    onMutate: async (todoId) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['todos'] });

      // Snapshot the previous value
      const previousTodos = queryClient.getQueryData(['todos']);

      // Optimistically update
      queryClient.setQueryData(['todos'], (old) =>
        old.map((todo) =>
          todo.id === todoId ? { ...todo, done: !todo.done } : todo
        )
      );

      // Return context with previous value
      return { previousTodos };
    },
    onError: (err, todoId, context) => {
      // Rollback on error
      queryClient.setQueryData(['todos'], context.previousTodos);
    },
    onSettled: () => {
      // Refetch after mutation completes
      queryClient.invalidateQueries({ queryKey: ['todos'] });
    },
  });

  return (
    <div>
      {/* render todos with toggle */}
      <button onClick={() => toggleTodo.mutate(todoId)}>Toggle</button>
    </div>
  );
}
```

## Mutation Lifecycle

Understanding the mutation lifecycle is crucial for optimistic updates:

```tsx
const mutation = useMutation({
  mutationFn: updateTodo,

  // 1. Before mutation function runs
  onMutate: async (variables) => {
    // Cancel queries, snapshot data, optimistically update
    // Return context object
    return { previousData };
  },

  // 2. If mutation succeeds
  onSuccess: (data, variables, context) => {
    // Handle successful mutation
    // data = mutation function response
    // variables = mutation variables
    // context = returned from onMutate
  },

  // 3. If mutation fails
  onError: (error, variables, context) => {
    // Rollback optimistic update
    // error = error object
    // context = returned from onMutate
  },

  // 4. Always runs after success or error
  onSettled: (data, error, variables, context) => {
    // Refetch to sync with server
  },
});
```

## Optimistic Update Patterns

### Adding an Item

```tsx
const addTodo = useMutation({
  mutationFn: (newTodo) => {
    return fetch('/api/todos', {
      method: 'POST',
      body: JSON.stringify(newTodo),
    }).then(res => res.json());
  },
  onMutate: async (newTodo) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previousTodos = queryClient.getQueryData(['todos']);

    // Add optimistic todo with temporary ID
    queryClient.setQueryData(['todos'], (old) => [
      ...old,
      { ...newTodo, id: 'temp-' + Date.now(), status: 'pending' },
    ]);

    return { previousTodos };
  },
  onError: (err, newTodo, context) => {
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSuccess: (data) => {
    // Replace temporary item with real server response
    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) =>
        todo.id.toString().startsWith('temp-') ? data : todo
      )
    );
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

### Updating an Item

```tsx
const updateTodo = useMutation({
  mutationFn: ({ id, updates }) => {
    return fetch(`/api/todos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }).then(res => res.json());
  },
  onMutate: async ({ id, updates }) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previousTodos = queryClient.getQueryData(['todos']);

    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) =>
        todo.id === id ? { ...todo, ...updates } : todo
      )
    );

    return { previousTodos };
  },
  onError: (err, variables, context) => {
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});

// Usage
updateTodo.mutate({ id: 1, updates: { title: 'Updated title' } });
```

### Deleting an Item

```tsx
const deleteTodo = useMutation({
  mutationFn: (todoId) => {
    return fetch(`/api/todos/${todoId}`, { method: 'DELETE' });
  },
  onMutate: async (todoId) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previousTodos = queryClient.getQueryData(['todos']);

    queryClient.setQueryData(['todos'], (old) =>
      old.filter((todo) => todo.id !== todoId)
    );

    return { previousTodos };
  },
  onError: (err, todoId, context) => {
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

## Multiple Query Updates

Update multiple related queries optimistically:

```tsx
const updateUser = useMutation({
  mutationFn: ({ userId, updates }) => {
    return fetch(`/api/users/${userId}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    }).then(res => res.json());
  },
  onMutate: async ({ userId, updates }) => {
    // Cancel all related queries
    await queryClient.cancelQueries({ queryKey: ['users'] });
    await queryClient.cancelQueries({ queryKey: ['user', userId] });

    // Snapshot previous data
    const previousUsers = queryClient.getQueryData(['users']);
    const previousUser = queryClient.getQueryData(['user', userId]);

    // Update users list
    queryClient.setQueryData(['users'], (old) =>
      old?.map((user) =>
        user.id === userId ? { ...user, ...updates } : user
      )
    );

    // Update individual user
    queryClient.setQueryData(['user', userId], (old) => ({
      ...old,
      ...updates,
    }));

    return { previousUsers, previousUser };
  },
  onError: (err, { userId }, context) => {
    // Rollback both queries
    queryClient.setQueryData(['users'], context.previousUsers);
    queryClient.setQueryData(['user', userId], context.previousUser);
  },
  onSettled: (data, error, { userId }) => {
    queryClient.invalidateQueries({ queryKey: ['users'] });
    queryClient.invalidateQueries({ queryKey: ['user', userId] });
  },
});
```

## Optimistic Updates with Infinite Queries

```tsx
const addPost = useMutation({
  mutationFn: (newPost) => {
    return fetch('/api/posts', {
      method: 'POST',
      body: JSON.stringify(newPost),
    }).then(res => res.json());
  },
  onMutate: async (newPost) => {
    await queryClient.cancelQueries({ queryKey: ['posts'] });
    const previousPosts = queryClient.getQueryData(['posts']);

    // Add to first page
    queryClient.setQueryData(['posts'], (old) => {
      if (!old?.pages.length) return old;

      return {
        ...old,
        pages: [
          {
            ...old.pages[0],
            posts: [
              { ...newPost, id: 'temp-' + Date.now() },
              ...old.pages[0].posts,
            ],
          },
          ...old.pages.slice(1),
        ],
      };
    });

    return { previousPosts };
  },
  onError: (err, newPost, context) => {
    queryClient.setQueryData(['posts'], context.previousPosts);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['posts'] });
  },
});
```

## UI Feedback During Optimistic Updates

### Show Pending State

```tsx
function TodoItem({ todo }) {
  const queryClient = useQueryClient();

  const toggleTodo = useMutation({
    mutationFn: (todoId) => fetch(`/api/todos/${todoId}/toggle`, { method: 'POST' }),
    onMutate: async (todoId) => {
      await queryClient.cancelQueries({ queryKey: ['todos'] });
      const previousTodos = queryClient.getQueryData(['todos']);

      queryClient.setQueryData(['todos'], (old) =>
        old.map((t) =>
          t.id === todoId
            ? { ...t, done: !t.done, isPending: true } // Mark as pending
            : t
        )
      );

      return { previousTodos };
    },
    onSuccess: (data, todoId) => {
      // Remove pending state
      queryClient.setQueryData(['todos'], (old) =>
        old.map((t) =>
          t.id === todoId ? { ...t, isPending: false } : t
        )
      );
    },
    onError: (err, todoId, context) => {
      queryClient.setQueryData(['todos'], context.previousTodos);
    },
  });

  return (
    <div className={todo.isPending ? 'opacity-50' : ''}>
      <input
        type="checkbox"
        checked={todo.done}
        onChange={() => toggleTodo.mutate(todo.id)}
        disabled={todo.isPending}
      />
      {todo.title}
    </div>
  );
}
```

### Show Error State

```tsx
const [error, setError] = useState(null);

const updateTodo = useMutation({
  mutationFn: updateTodoApi,
  onMutate: async (updates) => {
    setError(null); // Clear previous errors
    // ... optimistic update
  },
  onError: (err, variables, context) => {
    setError(err.message);
    // ... rollback
  },
});

return (
  <div>
    {error && <div className="error">{error}</div>}
    {/* render todo */}
  </div>
);
```

## Advanced Patterns

### Optimistic Update with Retry

```tsx
const updateTodo = useMutation({
  mutationFn: updateTodoApi,
  retry: 3,
  onMutate: async (updates) => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previousTodos = queryClient.getQueryData(['todos']);

    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) =>
        todo.id === updates.id
          ? { ...todo, ...updates, _optimistic: true }
          : todo
      )
    );

    return { previousTodos };
  },
  onSuccess: (data, variables) => {
    // Remove optimistic flag
    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) =>
        todo.id === variables.id
          ? { ...todo, _optimistic: false }
          : todo
      )
    );
  },
  onError: (err, variables, context) => {
    // Only rollback if all retries failed
    if (err.retryCount >= 3) {
      queryClient.setQueryData(['todos'], context.previousTodos);
    }
  },
});
```

### Debounced Optimistic Updates

For rapid updates like typing in a search or editing text:

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useDebouncedCallback } from 'use-debounce';

function TodoTitle({ todo }) {
  const queryClient = useQueryClient();
  const [localTitle, setLocalTitle] = useState(todo.title);

  const updateTodo = useMutation({
    mutationFn: ({ id, title }) => {
      return fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title }),
      }).then(res => res.json());
    },
    onMutate: async ({ id, title }) => {
      await queryClient.cancelQueries({ queryKey: ['todos'] });
      const previousTodos = queryClient.getQueryData(['todos']);

      queryClient.setQueryData(['todos'], (old) =>
        old.map((t) => (t.id === id ? { ...t, title } : t))
      );

      return { previousTodos };
    },
    onError: (err, variables, context) => {
      queryClient.setQueryData(['todos'], context.previousTodos);
      setLocalTitle(context.previousTodos.find(t => t.id === variables.id).title);
    },
  });

  const debouncedUpdate = useDebouncedCallback(
    (id, title) => updateTodo.mutate({ id, title }),
    500
  );

  const handleChange = (e) => {
    const newTitle = e.target.value;
    setLocalTitle(newTitle);
    debouncedUpdate(todo.id, newTitle);
  };

  return <input value={localTitle} onChange={handleChange} />;
}
```

### Optimistic Delete with Undo

```tsx
function TodoItem({ todo }) {
  const queryClient = useQueryClient();
  const [showUndo, setShowUndo] = useState(false);

  const deleteTodo = useMutation({
    mutationFn: (todoId) => {
      return fetch(`/api/todos/${todoId}`, { method: 'DELETE' });
    },
    onMutate: async (todoId) => {
      setShowUndo(true);
      await queryClient.cancelQueries({ queryKey: ['todos'] });
      const previousTodos = queryClient.getQueryData(['todos']);

      queryClient.setQueryData(['todos'], (old) =>
        old.filter((t) => t.id !== todoId)
      );

      // Auto-hide undo after 5 seconds
      setTimeout(() => setShowUndo(false), 5000);

      return { previousTodos };
    },
    onError: (err, todoId, context) => {
      queryClient.setQueryData(['todos'], context.previousTodos);
      setShowUndo(false);
    },
  });

  const handleUndo = () => {
    deleteTodo.reset(); // Reset mutation state
    queryClient.invalidateQueries({ queryKey: ['todos'] });
    setShowUndo(false);
  };

  if (showUndo) {
    return (
      <div className="undo-banner">
        Todo deleted <button onClick={handleUndo}>Undo</button>
      </div>
    );
  }

  return (
    <div>
      {todo.title}
      <button onClick={() => deleteTodo.mutate(todo.id)}>Delete</button>
    </div>
  );
}
```

### Batch Optimistic Updates

```tsx
const markAllDone = useMutation({
  mutationFn: () => {
    return fetch('/api/todos/mark-all-done', { method: 'POST' });
  },
  onMutate: async () => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });
    const previousTodos = queryClient.getQueryData(['todos']);

    queryClient.setQueryData(['todos'], (old) =>
      old.map((todo) => ({ ...todo, done: true }))
    );

    return { previousTodos };
  },
  onError: (err, variables, context) => {
    queryClient.setQueryData(['todos'], context.previousTodos);
  },
  onSettled: () => {
    queryClient.invalidateQueries({ queryKey: ['todos'] });
  },
});
```

## Cancel In-Flight Mutations

Cancel mutations that are no longer needed:

```tsx
function QuickEdit({ todo }) {
  const queryClient = useQueryClient();

  const updateTodo = useMutation({
    mutationFn: ({ id, title }) => {
      return fetch(`/api/todos/${id}`, {
        method: 'PATCH',
        body: JSON.stringify({ title }),
      }).then(res => res.json());
    },
    onMutate: async ({ id, title }) => {
      // Cancel previous mutations for this todo
      queryClient.cancelMutations({ mutationKey: ['updateTodo', id] });

      await queryClient.cancelQueries({ queryKey: ['todos'] });
      const previousTodos = queryClient.getQueryData(['todos']);

      queryClient.setQueryData(['todos'], (old) =>
        old.map((t) => (t.id === id ? { ...t, title } : t))
      );

      return { previousTodos };
    },
  });

  return (
    <input
      onChange={(e) => updateTodo.mutate({ id: todo.id, title: e.target.value })}
    />
  );
}
```

### Known Issues (Fixed)

- **initialData mount timing (fixed v5.87.1):** When using `initialData` with optimistic updates, a race condition could cause the optimistic value to be overwritten by `initialData` on component remount during the mutation. Fixed in v5.87.1 - if you see stale data flash after optimistic updates, upgrade to this version or later.

## Best Practices

1. **Always Cancel Queries**
   ```tsx
   await queryClient.cancelQueries({ queryKey: ['todos'] });
   ```
   Prevents race conditions between optimistic update and ongoing fetches.

2. **Always Return Context**
   ```tsx
   onMutate: async (variables) => {
     const previousData = queryClient.getQueryData(['todos']);
     // ... update
     return { previousData }; // Critical for rollback
   }
   ```

3. **Always Handle Errors**
   ```tsx
   onError: (err, variables, context) => {
     queryClient.setQueryData(['todos'], context.previousData);
   }
   ```

4. **Use onSettled for Refetch**
   ```tsx
   onSettled: () => {
     queryClient.invalidateQueries({ queryKey: ['todos'] });
   }
   ```
   Ensures data stays in sync with server.

5. **Show Visual Feedback**
   - Add loading/pending states to optimistically updated items
   - Show error messages on failure
   - Provide undo functionality where appropriate

6. **Handle Multiple Related Queries**
   - Update all queries that display the same data
   - Rollback all queries on error

7. **Consider Using Temporary IDs**
   - For created items, use temp IDs until server responds
   - Replace with server IDs on success

8. **Test Error Cases**
   - Verify rollback works correctly
   - Test network failures
   - Test validation errors from server

9. **Use queryOptions() for Type Safety**
   ```tsx
   const todosOptions = queryOptions({
     queryKey: ['todos'],
     queryFn: fetchTodos,
   });

   // Reuse in mutation callbacks for consistent types
   onMutate: async () => {
     const previous = queryClient.getQueryData(todosOptions.queryKey);
     // TypeScript knows the exact type of previous
     return { previous };
   }
   ```
