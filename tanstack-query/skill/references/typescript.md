# TypeScript Guide

TanStack Query v5 is written in TypeScript and provides excellent type safety and inference out of the box.

## Basic Type Inference

TanStack Query infers types from your query function return values:

```tsx
import { useQuery } from '@tanstack/react-query';

interface Todo {
  id: number;
  title: string;
  done: boolean;
}

function useTodos() {
  return useQuery({
    queryKey: ['todos'],
    queryFn: async (): Promise<Todo[]> => {
      const res = await fetch('/api/todos');
      return res.json();
    },
  });
}

function TodoList() {
  const { data } = useTodos();
  // data is automatically typed as Todo[] | undefined

  return (
    <ul>
      {data?.map((todo) => (
        // todo is typed as Todo
        <li key={todo.id}>{todo.title}</li>
      ))}
    </ul>
  );
}
```

## Typing Query Functions

### Inline Query Functions

```tsx
const { data } = useQuery({
  queryKey: ['todo', todoId],
  queryFn: async (): Promise<Todo> => {
    const res = await fetch(`/api/todos/${todoId}`);
    if (!res.ok) throw new Error('Failed to fetch');
    return res.json();
  },
});
// data is typed as Todo | undefined
```

### Extracted Query Functions

```tsx
async function fetchTodo(id: number): Promise<Todo> {
  const res = await fetch(`/api/todos/${id}`);
  if (!res.ok) throw new Error('Failed to fetch');
  return res.json();
}

const { data } = useQuery({
  queryKey: ['todo', todoId],
  queryFn: () => fetchTodo(todoId),
});
// data is automatically typed as Todo | undefined
```

### Query Functions with QueryKey

Access the query key in your function with proper typing:

```tsx
import { QueryFunction } from '@tanstack/react-query';

const fetchTodo: QueryFunction<Todo, ['todo', number]> = async ({ queryKey }) => {
  const [_, id] = queryKey;
  // id is typed as number
  const res = await fetch(`/api/todos/${id}`);
  return res.json();
};

const { data } = useQuery({
  queryKey: ['todo', todoId],
  queryFn: fetchTodo,
});
```

## Typing Mutations

### Basic Mutation Types

```tsx
import { useMutation } from '@tanstack/react-query';

interface CreateTodoInput {
  title: string;
  done?: boolean;
}

interface CreateTodoResponse {
  id: number;
  title: string;
  done: boolean;
  createdAt: string;
}

const mutation = useMutation({
  mutationFn: async (input: CreateTodoInput): Promise<CreateTodoResponse> => {
    const res = await fetch('/api/todos', {
      method: 'POST',
      body: JSON.stringify(input),
    });
    return res.json();
  },
});

// TypeScript knows:
// - mutation.mutate expects CreateTodoInput
// - mutation.data is CreateTodoResponse | undefined
mutation.mutate({ title: 'New Todo' });
```

### Generic Mutation Type

```tsx
import { UseMutationResult } from '@tanstack/react-query';

type CreateTodoMutation = UseMutationResult<
  CreateTodoResponse, // TData - successful response
  Error,              // TError - error type
  CreateTodoInput,    // TVariables - mutation input
  unknown             // TContext - context from onMutate
>;

function useCreateTodo(): CreateTodoMutation {
  return useMutation({
    mutationFn: async (input: CreateTodoInput): Promise<CreateTodoResponse> => {
      const res = await fetch('/api/todos', {
        method: 'POST',
        body: JSON.stringify(input),
      });
      return res.json();
    },
  });
}
```

## Error Typing

### Typed Errors

```tsx
interface ApiError {
  message: string;
  code: string;
  details?: Record<string, string>;
}

const { data, error } = useQuery<Todo[], ApiError>({
  queryKey: ['todos'],
  queryFn: async () => {
    const res = await fetch('/api/todos');
    if (!res.ok) {
      const errorData: ApiError = await res.json();
      throw errorData;
    }
    return res.json();
  },
});

if (error) {
  // error is typed as ApiError
  console.log(error.message);
  console.log(error.code);
}
```

### Error Type Narrowing

```tsx
function TodoList() {
  const { data, error, isError } = useQuery<Todo[], ApiError>({
    queryKey: ['todos'],
    queryFn: fetchTodos,
  });

  if (isError) {
    // TypeScript knows error is ApiError here
    return <div>Error: {error.message} (Code: {error.code})</div>;
  }

  // TypeScript knows data is Todo[] | undefined here
  return <div>{data?.map(todo => <TodoItem key={todo.id} todo={todo} />)}</div>;
}
```

## Generic Type Parameters

### useQuery Generics

```tsx
useQuery<
  TData,      // Type of data returned (inferred from queryFn)
  TError,     // Type of errors (default: Error)
  TQueryKey   // Type of query key (inferred)
>({ /* ... */ });
```

Example with all generics:

```tsx
interface User {
  id: number;
  name: string;
}

interface UserError {
  message: string;
  statusCode: number;
}

const { data, error } = useQuery<User, UserError, ['user', number]>({
  queryKey: ['user', userId],
  queryFn: async ({ queryKey }): Promise<User> => {
    const [_, id] = queryKey;
    const res = await fetch(`/api/users/${id}`);
    if (!res.ok) {
      throw { message: 'Failed to fetch', statusCode: res.status };
    }
    return res.json();
  },
});
```

### useMutation Generics

```tsx
useMutation<
  TData,      // Type of successful response
  TError,     // Type of error
  TVariables, // Type of mutation variables
  TContext    // Type of context from onMutate
>({ /* ... */ });
```

Example:

```tsx
interface UpdateTodoInput {
  id: number;
  title?: string;
  done?: boolean;
}

interface UpdateTodoResponse {
  id: number;
  title: string;
  done: boolean;
  updatedAt: string;
}

interface UpdateTodoContext {
  previousTodos: Todo[];
}

const mutation = useMutation<
  UpdateTodoResponse,
  ApiError,
  UpdateTodoInput,
  UpdateTodoContext
>({
  mutationFn: async (input) => {
    const res = await fetch(`/api/todos/${input.id}`, {
      method: 'PATCH',
      body: JSON.stringify(input),
    });
    return res.json();
  },
  onMutate: async (variables) => {
    const previousTodos = queryClient.getQueryData<Todo[]>(['todos']) ?? [];
    // Must return UpdateTodoContext
    return { previousTodos };
  },
  onError: (error, variables, context) => {
    // error: ApiError
    // variables: UpdateTodoInput
    // context: UpdateTodoContext | undefined
    if (context) {
      queryClient.setQueryData(['todos'], context.previousTodos);
    }
  },
});
```

## Typing QueryClient Methods

### setQueryData

```tsx
const queryClient = useQueryClient();

// Type-safe setQueryData
queryClient.setQueryData<Todo[]>(['todos'], (old) => {
  // old is typed as Todo[] | undefined
  return old ? [...old, newTodo] : [newTodo];
});
```

### getQueryData

```tsx
const todos = queryClient.getQueryData<Todo[]>(['todos']);
// todos is typed as Todo[] | undefined

if (todos) {
  // TypeScript knows todos is Todo[] here
  console.log(todos.length);
}

// v5.80.0+: When using queryOptions(), getQueryData infers types automatically
import { queryOptions } from '@tanstack/react-query';

const todosOptions = queryOptions({
  queryKey: ['todos'],
  queryFn: fetchTodos, // returns Todo[]
});

const cached = queryClient.getQueryData(todosOptions.queryKey);
// cached is typed as Todo[] | undefined - no manual generic needed
```

### invalidateQueries

```tsx
// Type-safe query key
queryClient.invalidateQueries({ queryKey: ['todos'] });
queryClient.invalidateQueries({ queryKey: ['todo', todoId] });
```

## Typing Infinite Queries

### Basic Infinite Query

```tsx
interface PostsPage {
  posts: Post[];
  nextCursor: number | null;
}

const { data } = useInfiniteQuery<PostsPage>({
  queryKey: ['posts'],
  queryFn: async ({ pageParam = 0 }): Promise<PostsPage> => {
    const res = await fetch(`/api/posts?cursor=${pageParam}`);
    return res.json();
  },
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
});

// data.pages is typed as PostsPage[]
data?.pages.forEach((page) => {
  // page is typed as PostsPage
  page.posts.forEach((post) => {
    // post is typed as Post
    console.log(post.title);
  });
});
```

### Infinite Query with Generics

```tsx
useInfiniteQuery<
  TData,         // Type of page data
  TError,        // Type of error
  TQueryData,    // Type of transformed data (from select)
  TQueryKey,     // Type of query key
  TPageParam     // Type of page parameter
>({ /* ... */ });
```

Example:

```tsx
const { data } = useInfiniteQuery<
  PostsPage,
  ApiError,
  PostsPage,
  ['posts', string],
  number
>({
  queryKey: ['posts', filter],
  queryFn: async ({ pageParam }): Promise<PostsPage> => {
    const res = await fetch(`/api/posts?cursor=${pageParam}&filter=${filter}`);
    return res.json();
  },
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
});
```

## Typing Select Transformations

### Transform Query Data

```tsx
interface TodoApiResponse {
  id: number;
  title: string;
  completed: boolean;
}

interface Todo {
  id: number;
  title: string;
  done: boolean; // renamed from completed
}

const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: async (): Promise<TodoApiResponse[]> => {
    const res = await fetch('/api/todos');
    return res.json();
  },
  select: (data): Todo[] => {
    // data is typed as TodoApiResponse[]
    return data.map(todo => ({
      id: todo.id,
      title: todo.title,
      done: todo.completed, // transform
    }));
  },
});

// data is now typed as Todo[] | undefined
```

### Partial Selection

```tsx
interface User {
  id: number;
  name: string;
  email: string;
  role: string;
  metadata: Record<string, unknown>;
}

const { data } = useQuery({
  queryKey: ['user', userId],
  queryFn: async (): Promise<User> => {
    const res = await fetch(`/api/users/${userId}`);
    return res.json();
  },
  select: (user) => ({
    id: user.id,
    name: user.name,
  }),
});

// data is typed as { id: number; name: string } | undefined
```

## isPlaceholderData Type Narrowing

Since v5.65.0, `isPlaceholderData` properly narrows the data type:

```tsx
const { data, isPlaceholderData } = useQuery({
  queryKey: ['todos', page],
  queryFn: () => fetchTodos(page),
  placeholderData: (previousData) => previousData,
});

if (isPlaceholderData) {
  // data is narrowed to the placeholder type
  // TypeScript knows this is stale/previous data
}

if (!isPlaceholderData && data) {
  // data is narrowed to the fresh query result type
  // Safe to use without additional type guards
}
```

## Custom Hooks with Types

### Reusable Typed Hooks

```tsx
interface UseTodoOptions {
  refetchInterval?: number;
  enabled?: boolean;
}

function useTodo(id: number, options?: UseTodoOptions) {
  return useQuery<Todo, ApiError>({
    queryKey: ['todo', id],
    queryFn: async (): Promise<Todo> => {
      const res = await fetch(`/api/todos/${id}`);
      if (!res.ok) {
        const error: ApiError = await res.json();
        throw error;
      }
      return res.json();
    },
    refetchInterval: options?.refetchInterval,
    enabled: options?.enabled,
  });
}

// Usage with full type safety
const { data, error, isLoading } = useTodo(1, { refetchInterval: 5000 });
```

### Generic Custom Hooks

```tsx
function useResource<T>(resourceType: string, id: number) {
  return useQuery<T, ApiError>({
    queryKey: [resourceType, id],
    queryFn: async (): Promise<T> => {
      const res = await fetch(`/api/${resourceType}/${id}`);
      if (!res.ok) throw await res.json();
      return res.json();
    },
  });
}

// Usage
const { data: user } = useResource<User>('users', 1);
// data is typed as User | undefined

const { data: post } = useResource<Post>('posts', 123);
// data is typed as Post | undefined
```

## Typing Query Keys

### Const Query Keys

```tsx
const todoKeys = {
  all: ['todos'] as const,
  lists: () => [...todoKeys.all, 'list'] as const,
  list: (filters: string) => [...todoKeys.lists(), filters] as const,
  details: () => [...todoKeys.all, 'detail'] as const,
  detail: (id: number) => [...todoKeys.details(), id] as const,
};

// Type-safe query keys
useQuery({
  queryKey: todoKeys.detail(todoId),
  queryFn: () => fetchTodo(todoId),
});

// Type-safe invalidation
queryClient.invalidateQueries({ queryKey: todoKeys.all });
queryClient.invalidateQueries({ queryKey: todoKeys.detail(todoId) });
```

**QueryFilters with partial keys and readonly (v5.90.8+):**

`QueryFilters` now supports partial query keys and preserves `readonly` from `as const` assertions, so you can filter by key prefix without losing type safety:

```tsx
// as const works seamlessly with QueryFilters
queryClient.invalidateQueries({ queryKey: todoKeys.all }); // readonly ['todos']
```

### QueryKey Type Helper

```tsx
import { QueryKey } from '@tanstack/react-query';

type TodoQueryKey = ['todos'] | ['todos', 'list', string] | ['todos', 'detail', number];

function useTodoQuery(key: TodoQueryKey) {
  return useQuery({
    queryKey: key,
    queryFn: async () => {
      // Implementation based on key
    },
  });
}
```

## Typing Mutation Context

### Context with Optimistic Updates

```tsx
interface UpdateTodoVariables {
  id: number;
  updates: Partial<Todo>;
}

interface UpdateTodoContext {
  previousTodos: Todo[];
  previousTodo: Todo;
  rollback: () => void;
}

const mutation = useMutation<
  Todo,
  ApiError,
  UpdateTodoVariables,
  UpdateTodoContext
>({
  mutationFn: async ({ id, updates }) => {
    const res = await fetch(`/api/todos/${id}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
    return res.json();
  },
  onMutate: async ({ id, updates }): Promise<UpdateTodoContext> => {
    await queryClient.cancelQueries({ queryKey: ['todos'] });

    const previousTodos = queryClient.getQueryData<Todo[]>(['todos']) ?? [];
    const previousTodo = queryClient.getQueryData<Todo>(['todo', id])!;

    // Optimistic update
    queryClient.setQueryData<Todo[]>(['todos'], (old) =>
      old?.map((todo) => (todo.id === id ? { ...todo, ...updates } : todo))
    );

    const rollback = () => {
      queryClient.setQueryData(['todos'], previousTodos);
      queryClient.setQueryData(['todo', id], previousTodo);
    };

    return { previousTodos, previousTodo, rollback };
  },
  onError: (_error, _variables, context) => {
    // context is typed as UpdateTodoContext | undefined
    context?.rollback();
  },
});
```

## Type-Safe Query Options

### queryOptions() Helper (Recommended)

The `queryOptions()` helper creates reusable, fully type-safe query configurations:

```tsx
import { queryOptions, useQuery, useQueryClient } from '@tanstack/react-query';

function todoQueryOptions(id: number) {
  return queryOptions({
    queryKey: ['todo', id] as const,
    queryFn: () => fetchTodo(id),
    staleTime: 1000 * 60 * 5,
  });
}

// Full type inference - no manual generics needed
const { data } = useQuery(todoQueryOptions(todoId));
// data is typed as Todo | undefined

// Works with prefetching
queryClient.prefetchQuery(todoQueryOptions(todoId));

// Works with getQueryData
const cached = queryClient.getQueryData(todoQueryOptions(todoId).queryKey);
// cached is typed as Todo | undefined

// Works with invalidation
queryClient.invalidateQueries({ queryKey: todoQueryOptions(todoId).queryKey });
```

### Manual Query Options (Alternative)

```tsx
import { UseQueryOptions } from '@tanstack/react-query';

type TodoQueryOptions = UseQueryOptions<Todo, ApiError, Todo, ['todo', number]>;

const defaultTodoOptions: Partial<TodoQueryOptions> = {
  staleTime: 1000 * 60 * 5,
  retry: 3,
};

function useTodo(id: number, options?: Partial<TodoQueryOptions>) {
  return useQuery<Todo, ApiError>({
    queryKey: ['todo', id],
    queryFn: () => fetchTodo(id),
    ...defaultTodoOptions,
    ...options,
  });
}
```

## Strict Type Safety

### Enable Strict Mode

```tsx
// tsconfig.json
{
  "compilerOptions": {
    "strict": true,
    "strictNullChecks": true,
    "noImplicitAny": true
  }
}
```

### Avoid Type Assertions

```tsx
// ❌ Bad - using type assertion
const data = queryClient.getQueryData(['todos']) as Todo[];

// ✅ Good - proper type checking
const data = queryClient.getQueryData<Todo[]>(['todos']);
if (data) {
  // TypeScript knows data is Todo[] here
  console.log(data.length);
}
```

### Non-Null Assertions

Use sparingly and only when you're certain:

```tsx
// ❌ Risky
const todos = queryClient.getQueryData<Todo[]>(['todos'])!;

// ✅ Better
const todos = queryClient.getQueryData<Todo[]>(['todos']);
if (!todos) {
  throw new Error('Todos not found in cache');
}
// Now safe to use todos
```

## Typing DevTools

```tsx
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <YourApp />
      {/* TypeScript will check props */}
      <ReactQueryDevtools
        initialIsOpen={false}
        buttonPosition="bottom-right"
      />
    </QueryClientProvider>
  );
}
```

## Common Type Issues

### Issue: Cannot infer type from async function

```tsx
// ❌ Problem
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: async () => {
    const res = await fetch('/api/todos');
    return res.json(); // Returns any
  },
});

// ✅ Solution 1: Add return type to queryFn
const { data } = useQuery({
  queryKey: ['todos'],
  queryFn: async (): Promise<Todo[]> => {
    const res = await fetch('/api/todos');
    return res.json();
  },
});

// ✅ Solution 2: Use generic parameter
const { data } = useQuery<Todo[]>({
  queryKey: ['todos'],
  queryFn: async () => {
    const res = await fetch('/api/todos');
    return res.json();
  },
});
```

### Issue: Context type mismatch

```tsx
// ❌ Problem - context type doesn't match
const mutation = useMutation({
  mutationFn: updateTodo,
  onMutate: () => {
    return { previous: [] }; // Returns wrong type
  },
  onError: (err, vars, context) => {
    context.previousTodos; // Error: previousTodos doesn't exist
  },
});

// ✅ Solution - Define context interface
interface MutationContext {
  previousTodos: Todo[];
}

const mutation = useMutation<Todo, Error, UpdateInput, MutationContext>({
  mutationFn: updateTodo,
  onMutate: async (): Promise<MutationContext> => {
    const previousTodos = queryClient.getQueryData<Todo[]>(['todos']) ?? [];
    return { previousTodos };
  },
  onError: (err, vars, context) => {
    if (context) {
      context.previousTodos; // ✅ Properly typed
    }
  },
});
```

## Best Practices

1. **Always type your query functions**
   ```tsx
   queryFn: async (): Promise<Todo[]> => { /* ... */ }
   ```

2. **Use type inference when possible**
   ```tsx
   // Let TanStack Query infer types from queryFn return type
   const { data } = useQuery({
     queryKey: ['todos'],
     queryFn: async (): Promise<Todo[]> => fetchTodos(),
   });
   // data is automatically Todo[] | undefined
   ```

3. **Define error types**
   ```tsx
   const { error } = useQuery<Todo[], ApiError>({ /* ... */ });
   ```

4. **Use const assertions for query keys**
   ```tsx
   const todoKeys = {
     all: ['todos'] as const,
     detail: (id: number) => ['todos', id] as const,
   };
   ```

5. **Create reusable typed hooks**
   ```tsx
   function useTodo(id: number) {
     return useQuery<Todo, ApiError>({ /* ... */ });
   }
   ```

6. **Type mutation context for optimistic updates**
   ```tsx
   useMutation<TData, TError, TVariables, TContext>({ /* ... */ })
   ```

7. **Use strict TypeScript settings**
   ```json
   {
     "strict": true,
     "strictNullChecks": true
   }
   ```

8. **Avoid type assertions**
   - Use type parameters instead
   - Check for undefined/null before using data
