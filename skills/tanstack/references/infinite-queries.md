# Infinite Queries

Infinite queries are used for implementing "load more" and infinite scroll patterns. They allow you to fetch paginated data progressively.

## Basic Infinite Query

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';

function Posts() {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: async ({ pageParam = 0 }) => {
      const res = await fetch(`/api/posts?cursor=${pageParam}`);
      return res.json();
    },
    initialPageParam: 0,
    getNextPageParam: (lastPage, allPages) => {
      // Return undefined if no more pages
      return lastPage.nextCursor ?? undefined;
    },
  });

  if (isLoading) return <div>Loading...</div>;

  return (
    <>
      {data.pages.map((page, i) => (
        <div key={i}>
          {page.posts.map((post) => (
            <div key={post.id}>{post.title}</div>
          ))}
        </div>
      ))}
      <button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        {isFetchingNextPage
          ? 'Loading more...'
          : hasNextPage
          ? 'Load More'
          : 'Nothing more to load'}
      </button>
    </>
  );
}
```

## Data Structure

The `data` object has a specific structure:

```tsx
{
  pages: [
    { posts: [...], nextCursor: 1 },  // Page 1
    { posts: [...], nextCursor: 2 },  // Page 2
    { posts: [...], nextCursor: 3 },  // Page 3
  ],
  pageParams: [0, 1, 2] // The pageParam values used
}
```

## Page Parameters

### initialPageParam

Required parameter that specifies the initial page parameter:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: ({ pageParam }) => fetchPosts(pageParam),
  initialPageParam: 0, // or 1, or { cursor: null }, etc.
  getNextPageParam: (lastPage) => lastPage.nextCursor,
});
```

### getNextPageParam

Function that receives the last page and all pages, and returns the next page parameter:

```tsx
// Cursor-based pagination
getNextPageParam: (lastPage, allPages) => {
  return lastPage.nextCursor ?? undefined;
}

// Offset-based pagination
getNextPageParam: (lastPage, allPages) => {
  if (lastPage.length === 0) return undefined;
  return allPages.length * 10; // Assuming 10 items per page
}

// Page number pagination
getNextPageParam: (lastPage, allPages) => {
  const totalPages = lastPage.totalPages;
  const nextPage = allPages.length + 1;
  return nextPage <= totalPages ? nextPage : undefined;
}

// Access to all pages
getNextPageParam: (lastPage, allPages) => {
  const totalFetched = allPages.reduce((acc, page) => acc + page.data.length, 0);
  return totalFetched < lastPage.total ? lastPage.nextCursor : undefined;
}
```

### getPreviousPageParam

For bidirectional infinite scrolling:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: ({ pageParam }) => fetchPosts(pageParam),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  getPreviousPageParam: (firstPage) => firstPage.previousCursor,
});
```

## Fetching Pages

### Fetch Next Page

```tsx
const { fetchNextPage, hasNextPage, isFetchingNextPage } = useInfiniteQuery({
  // ...config
});

// Manual trigger
<button onClick={() => fetchNextPage()} disabled={!hasNextPage}>
  Load More
</button>

// Infinite scroll
useEffect(() => {
  const handleScroll = () => {
    if (
      window.innerHeight + window.scrollY >= document.body.offsetHeight - 500 &&
      hasNextPage &&
      !isFetchingNextPage
    ) {
      fetchNextPage();
    }
  };

  window.addEventListener('scroll', handleScroll);
  return () => window.removeEventListener('scroll', handleScroll);
}, [fetchNextPage, hasNextPage, isFetchingNextPage]);
```

### Fetch Previous Page

```tsx
const { fetchPreviousPage, hasPreviousPage, isFetchingPreviousPage } = useInfiniteQuery({
  // ...config
});

<button onClick={() => fetchPreviousPage()} disabled={!hasPreviousPage}>
  Load Previous
</button>
```

## Pagination Strategies

### Cursor-Based Pagination

Best for real-time data and when items can be inserted/deleted:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: async ({ pageParam }) => {
    const res = await fetch(`/api/posts?cursor=${pageParam}&limit=10`);
    return res.json();
  },
  initialPageParam: null,
  getNextPageParam: (lastPage) => lastPage.nextCursor ?? undefined,
});

// API response structure:
// {
//   data: [...],
//   nextCursor: 'cursor_string' | null
// }
```

### Offset-Based Pagination

Simpler but can have issues with real-time data:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: async ({ pageParam = 0 }) => {
    const res = await fetch(`/api/posts?offset=${pageParam}&limit=10`);
    return res.json();
  },
  initialPageParam: 0,
  getNextPageParam: (lastPage, allPages) => {
    if (lastPage.data.length < 10) return undefined;
    return allPages.length * 10;
  },
});
```

### Page Number Pagination

Traditional page-based approach:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: async ({ pageParam = 1 }) => {
    const res = await fetch(`/api/posts?page=${pageParam}&size=10`);
    return res.json();
  },
  initialPageParam: 1,
  getNextPageParam: (lastPage, allPages) => {
    const currentPage = allPages.length;
    return currentPage < lastPage.totalPages ? currentPage + 1 : undefined;
  },
});
```

## Infinite Scroll Implementation

### Using Intersection Observer

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';
import { useRef, useCallback } from 'react';

function InfiniteScrollPosts() {
  const observerTarget = useRef(null);

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam = 0 }) => fetchPosts(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  // Setup intersection observer
  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          fetchNextPage();
        }
      },
      { threshold: 1.0 }
    );

    if (observerTarget.current) {
      observer.observe(observerTarget.current);
    }

    return () => observer.disconnect();
  }, [fetchNextPage, hasNextPage, isFetchingNextPage]);

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      ))}
      {hasNextPage && (
        <div ref={observerTarget} className="loading-indicator">
          {isFetchingNextPage ? 'Loading more...' : 'Load more'}
        </div>
      )}
    </div>
  );
}
```

### Using react-intersection-observer

```tsx
import { useInfiniteQuery } from '@tanstack/react-query';
import { useInView } from 'react-intersection-observer';

function InfiniteScrollPosts() {
  const { ref, inView } = useInView();

  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam = 0 }) => fetchPosts(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, fetchNextPage, hasNextPage, isFetchingNextPage]);

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.posts.map((post) => (
            <PostCard key={post.id} post={post} />
          ))}
        </div>
      ))}
      <div ref={ref}>{isFetchingNextPage && 'Loading...'}</div>
    </div>
  );
}
```

## Refetching and Invalidation

### Refetch All Pages

```tsx
const queryClient = useQueryClient();

// Refetch all pages
queryClient.invalidateQueries({ queryKey: ['posts'] });

// Or manually
const { refetch } = useInfiniteQuery({ /* ... */ });
refetch();
```

### Refetch Only First Page

```tsx
queryClient.invalidateQueries({
  queryKey: ['posts'],
  refetchPage: (page, index) => index === 0,
});
```

### Refetch Specific Pages

```tsx
// Refetch first 3 pages
queryClient.invalidateQueries({
  queryKey: ['posts'],
  refetchPage: (page, index) => index < 3,
});

// Refetch based on page content
queryClient.invalidateQueries({
  queryKey: ['posts'],
  refetchPage: (page, index) => {
    // Refetch if page has a specific item
    return page.posts.some(post => post.id === targetId);
  },
});
```

## Transforming Data

### Flatten Pages

```tsx
const { data } = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  select: (data) => ({
    pages: [...data.pages],
    pageParams: [...data.pageParams],
    // Flatten all posts
    allPosts: data.pages.flatMap(page => page.posts),
  }),
});

// Now you can use data.allPosts directly
return <div>{data?.allPosts.map(post => <PostCard key={post.id} post={post} />)}</div>;
```

### Filter and Transform

```tsx
const { data } = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  select: (data) => ({
    ...data,
    pages: data.pages.map(page => ({
      ...page,
      posts: page.posts.filter(post => !post.isDeleted),
    })),
  }),
});
```

## Bidirectional Infinite Scrolling

```tsx
function BidirectionalScroll() {
  const {
    data,
    fetchNextPage,
    fetchPreviousPage,
    hasNextPage,
    hasPreviousPage,
    isFetchingNextPage,
    isFetchingPreviousPage,
  } = useInfiniteQuery({
    queryKey: ['messages'],
    queryFn: ({ pageParam }) => fetchMessages(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    getPreviousPageParam: (firstPage) => firstPage.previousCursor,
  });

  return (
    <div>
      <button
        onClick={() => fetchPreviousPage()}
        disabled={!hasPreviousPage || isFetchingPreviousPage}
      >
        {isFetchingPreviousPage ? 'Loading...' : 'Load Older'}
      </button>

      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.messages.map((message) => (
            <MessageCard key={message.id} message={message} />
          ))}
        </div>
      ))}

      <button
        onClick={() => fetchNextPage()}
        disabled={!hasNextPage || isFetchingNextPage}
      >
        {isFetchingNextPage ? 'Loading...' : 'Load Newer'}
      </button>
    </div>
  );
}
```

## Advanced Patterns

### Search with Infinite Scroll

```tsx
function SearchResults({ searchTerm }) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isFetchingNextPage,
  } = useInfiniteQuery({
    queryKey: ['search', searchTerm],
    queryFn: ({ pageParam = 0 }) =>
      fetch(`/api/search?q=${searchTerm}&cursor=${pageParam}`).then(r => r.json()),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
    enabled: searchTerm.length > 2, // Only search if term is long enough
  });

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.results.map((result) => (
            <SearchResult key={result.id} result={result} />
          ))}
        </div>
      ))}
      {hasNextPage && (
        <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}>
          Load More Results
        </button>
      )}
    </div>
  );
}
```

### Infinite Query with Filters

```tsx
function FilteredList({ filters }) {
  const {
    data,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ['items', filters],
    queryFn: ({ pageParam = 0 }) =>
      fetchItems({ ...filters, cursor: pageParam }),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  // When filters change, query automatically resets and refetches from page 1

  return (
    <div>
      {data?.pages.map((page, i) => (
        <div key={i}>
          {page.items.map((item) => (
            <ItemCard key={item.id} item={item} />
          ))}
        </div>
      ))}
      {hasNextPage && <button onClick={() => fetchNextPage()}>Load More</button>}
    </div>
  );
}
```

### Prefetching Next Page

```tsx
function Posts() {
  const queryClient = useQueryClient();

  const {
    data,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ['posts'],
    queryFn: ({ pageParam = 0 }) => fetchPosts(pageParam),
    initialPageParam: 0,
    getNextPageParam: (lastPage) => lastPage.nextCursor,
  });

  // Prefetch next page when user is near the end
  useEffect(() => {
    if (hasNextPage) {
      const nextPageParam = data?.pageParams[data.pageParams.length - 1] + 1;
      queryClient.prefetchInfiniteQuery({
        queryKey: ['posts'],
        queryFn: ({ pageParam }) => fetchPosts(pageParam),
        initialPageParam: 0,
        getNextPageParam: (lastPage) => lastPage.nextCursor,
        pages: data?.pages.length + 1, // Prefetch one more page
      });
    }
  }, [data, hasNextPage, queryClient]);

  return <div>{/* render */}</div>;
}
```

## Streaming with Infinite Queries

`experimental_streamedQuery` can be combined with infinite patterns for streaming paginated data:

```tsx
import { experimental_streamedQuery as streamedQuery } from '@tanstack/react-query';

const { data, fetchStatus } = useInfiniteQuery({
  queryKey: ['stream-feed'],
  queryFn: streamedQuery({
    streamFn: ({ pageParam }) => fetchStreamedFeed(pageParam),
    refetchMode: 'append',
  }),
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage?.nextCursor,
});

// Each page streams in chunks while fetchStatus === 'fetching'
```

See the Streamed Queries section in the main SKILL.md for the full `streamedQuery` API.

## Common Issues and Solutions

### Duplicate Data After Invalidation

When invalidating an infinite query, it refetches all pages. To avoid duplicates.

**SSR note:** v5.90.3 fixed unhandled promise rejections during dehydration/rehydration of pending infinite queries. Ensure you're on v5.90.3+ if using SSR with infinite queries.

```tsx
// Option 1: Use refetchPage to only refetch specific pages
queryClient.invalidateQueries({
  queryKey: ['posts'],
  refetchPage: (page, index) => index === 0, // Only refetch first page
});

// Option 2: Reset to first page
queryClient.resetQueries({ queryKey: ['posts'] });
```

### Stale Data Between Pages

Set appropriate `staleTime`:

```tsx
useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  staleTime: 1000 * 60 * 5, // 5 minutes
});
```

### Managing Total Count

Track total items across all pages:

```tsx
const { data } = useInfiniteQuery({
  queryKey: ['posts'],
  queryFn: fetchPosts,
  initialPageParam: 0,
  getNextPageParam: (lastPage) => lastPage.nextCursor,
  select: (data) => ({
    ...data,
    totalCount: data.pages[0]?.total || 0, // Assuming API returns total
    currentCount: data.pages.reduce((acc, page) => acc + page.posts.length, 0),
  }),
});

// Display: Showing {data.currentCount} of {data.totalCount}
```

## Best Practices

1. **Choose the Right Pagination Strategy**
   - Use cursor-based for real-time feeds
   - Use offset for simple lists
   - Use page numbers for traditional pagination

2. **Handle Edge Cases**
   - Empty states when no data
   - Loading states for first page
   - Error states with retry
   - End of list indicators

3. **Optimize Performance**
   - Use `select` to transform data once
   - Set appropriate `staleTime` and `gcTime`
   - Implement virtual scrolling for large lists (react-window, react-virtualized)

4. **Refetch Strategies**
   - Only refetch first page for most updates
   - Use `refetchPage` for targeted refetches
   - Consider resetting queries when filters change

5. **User Experience**
   - Show loading indicators for next/previous pages
   - Disable buttons during fetching
   - Provide feedback when no more data
   - Handle errors gracefully with retry options
