# Async Basics

Rust's async is cooperative: `.await` is an explicit yield point. There is no built-in runtime; you pick one. In 2026, that runtime is `tokio` for almost every application. (If a tutorial hands you `async-std`, stop: it has been discontinued, carries a RustSec advisory for that reason, and its own site still shows no notice. `smol` is the named replacement.) This file covers what you need to write async Rust well from day 1, and the small set of pitfalls that cause most async bugs.

## Threads First, Async Second

Before any of this: **async is for I/O concurrency, not for speed.** If your work is CPU-bound - parsing, hashing, image processing, simulation - you want threads, and the standard library already gives you everything you need. Reaching for `tokio` because you want to "use all the cores" is the wrong tool.

```rust
use std::thread;
use std::sync::mpsc;

// Detached-ish: a handle you join to get the result back
let h = thread::spawn(|| expensive(1));   // must be 'static - move owned data in
let a = h.join().unwrap();                // Result: Err means the thread panicked

// Scoped threads: borrow from the stack, guaranteed joined at the end of the scope
let data = vec![1, 2, 3];
thread::scope(|s| {
    s.spawn(|| println!("{:?}", &data));   // &data borrow is fine here
    s.spawn(|| println!("{}", data.len()));
});                                        // both joined before this line returns

// Message passing: the idiomatic way to get results out
let (tx, rx) = mpsc::channel();
for id in 0..4 {
    let tx = tx.clone();
    thread::spawn(move || tx.send(work(id)).unwrap());
}
drop(tx);                                  // the last sender must drop or rx never ends
for result in rx { }                       // iterates until every sender is gone
```

`thread::scope` is the one worth remembering: it is what lets a thread borrow local data instead of forcing you to `Arc`-wrap everything, because the scope cannot exit until every thread inside it has finished. That `drop(tx)` is the classic hang - a receiver loop ends when all senders are dropped, and the original `tx` you cloned from is a sender.

For data parallelism over a collection, do not hand-roll any of this: `rayon`'s `.par_iter()` is one word and covers most of it (see `performance.md`).

## Mental Model

An `async fn` does not run when called. It returns a `Future`, which is a state machine. A runtime (`tokio`) drives futures by polling them; when a poll hits a point that needs to wait (network I/O, timer, channel receive), the future returns "not ready" and the runtime parks it until the underlying event fires.

```rust
async fn add(a: i32, b: i32) -> i32 { a + b }

let f = add(2, 3);   // f is a Future, nothing has run yet
let n = f.await;     // runtime drives f to completion; n == 5
```

`.await` only works inside `async fn` or `async {}` blocks.

## The Minimum You Need

```rust
// Cargo.toml
// [dependencies]
// tokio = { version = "1", features = ["full"] }

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let body = reqwest::get("https://example.com").await?.text().await?;
    println!("{}", body.len());
    Ok(())
}
```

`#[tokio::main]` is a macro that wraps `main` with the runtime setup. For tests, use `#[tokio::test]`.

```rust
#[tokio::test]
async fn it_works() {
    assert_eq!(add(2, 3).await, 5);
}
```

## `tokio` Features

`tokio = { version = "1", features = ["full"] }` is fine while learning. In production, narrow the feature list:

```toml
tokio = { version = "1", features = ["macros", "rt-multi-thread", "net", "fs", "sync", "time"] }
```

Common ones:
- `macros` - `#[tokio::main]`, `#[tokio::test]`, `tokio::select!`, `tokio::join!`
- `rt-multi-thread` - the default work-stealing runtime
- `rt` - single-threaded runtime (use this in WASM, embedded, or to avoid `Send` bounds)
- `net` - TCP/UDP
- `fs` - async filesystem
- `sync` - `Mutex`, `RwLock`, `mpsc`, `broadcast`, `oneshot`, `Notify`
- `time` - `sleep`, `interval`, `timeout`
- `process` - spawning subprocesses
- `signal` - Ctrl-C, SIGTERM handling

## Spawning Tasks

`tokio::spawn` puts a future on the runtime so it can run concurrently with the current task.

```rust
use tokio::time::{sleep, Duration};

#[tokio::main]
async fn main() {
    let handle = tokio::spawn(async {
        sleep(Duration::from_secs(1)).await;
        42
    });

    let result = handle.await.unwrap();   // wait for the spawned task
    println!("{result}");
}
```

`spawn` returns a `JoinHandle<T>`. Awaiting it gives you the task's return value (wrapped in `Result` to handle panic).

## `Send`, `Sync`, and `'static` Bounds

Tasks spawned with `tokio::spawn` must be `Send + 'static` because the runtime moves them across threads.

- `Send` means "safe to move to another thread."
- `Sync` means "safe to share by reference (`&T`) across threads."
- `'static` means "owns all its data; does not borrow from the spawning function's stack."

If you see `error: future cannot be sent between threads safely`, you have likely:
- Held a non-`Send` type across an `.await` (e.g., `Rc<T>`, `RefCell<T>`, `std::sync::MutexGuard`).
- Captured a reference instead of moving owned data into the task.

The most common fix: replace `Rc` with `Arc`, `RefCell` with `Mutex` (and check the next pitfall), and `move` the closure body into the task.

```rust
let data = Arc::new(some_data);

tokio::spawn({
    let data = Arc::clone(&data);     // clone Arc, move into task
    async move {
        process(&data).await;
    }
});
```

## The `MutexGuard` Across `.await` Pitfall

Holding a synchronous `std::sync::MutexGuard` across an `.await` is wrong:
1. The guard is not `Send`, so the future is not `Send`, so `tokio::spawn` rejects it.
2. Even when it compiles, you can deadlock: the task yields while still holding the lock, and another task waiting for the lock blocks the runtime thread.

Two fixes, depending on need:

**A. Drop the guard before the await:**
```rust
use std::sync::Mutex;
let state = Arc::new(Mutex::new(Counter::new()));

let snapshot = {
    let g = state.lock().unwrap();
    g.snapshot()       // get the data we need
};                     // guard dropped here
do_async_thing(snapshot).await;
```

**B. Use `tokio::sync::Mutex` (async-aware):**
```rust
use tokio::sync::Mutex;
let state = Arc::new(Mutex::new(Counter::new()));

let mut g = state.lock().await;     // this await is OK
do_async_thing(&mut g).await;       // holding the lock across await is OK
```

`tokio::sync::Mutex` is slower than `std::sync::Mutex`. Default to `std::sync::Mutex` and scope your locks tightly. Reach for `tokio::sync::Mutex` only when you genuinely need to hold a lock across awaits.

**Two different problems wear the same name.** Holding a `std::sync::MutexGuard` across `.await` is a *compile error* (the future stops being `Send`) - that one is not a judgment call, just fix it. Holding a `tokio::sync::Mutex` across `.await` compiles fine, and whether it is wrong is a *design* question. "Never hold a lock across an await" is repeated as though it settled both, and it does not.

The clearest case where holding it is exactly right is **single-flight**: guarding an expensive one-time load (a model, a connection pool, a parsed index) so that N concurrent cold-start callers coalesce into one load instead of N.

```rust
use tokio::sync::Mutex;

// Concurrent first-callers all block here; exactly one does the load.
let mut slot = cache.lock().await;
if slot.is_none() {
    *slot = Some(expensive_load().await);   // lock held across .await, deliberately
}
```

Drop the lock and each caller kicks off its own `expensive_load()`. Judge it by the numbers, not the slogan: an uncontended `tokio::sync::Mutex` acquire is tens to hundreds of nanoseconds, so if the work it guards is milliseconds long, the warm-path cost is noise and the coalescing is the whole point. If the warm path is genuinely hot, keep the load gate but serve warm reads without the lock (an `arc_swap::ArcSwapOption` read plus a `Mutex<()>` held only during the load).

## Don't Block the Runtime

Async runtimes assume tasks yield quickly. CPU-bound work (parsing big files, encoding video, expensive computations) starves other tasks. Two escapes:

**`tokio::task::spawn_blocking`** for synchronous, CPU-heavy work:
```rust
let result = tokio::task::spawn_blocking(|| expensive_computation()).await?;
```

**`tokio::task::block_in_place`** runs a blocking section inside the current async task without starving sibling tasks. It **panics on a `current_thread` runtime** - that is the constraint to remember. (Outside any runtime it is simply allowed, and just calls the closure normally, so a helper using it still works in a plain sync test.) It also suspends any other code running concurrently in the same task, e.g. under `join!`. Prefer `spawn_blocking`; reach for `block_in_place` only when the blocking work genuinely cannot move into its own task:
```rust
tokio::task::block_in_place(|| do_blocking_thing());
```

Never call `std::thread::sleep` in async code. Use `tokio::time::sleep`. Never call blocking I/O (`std::fs::read`, `std::net::TcpStream`) on a runtime thread. Use `tokio::fs`, `tokio::net`, or wrap with `spawn_blocking`.

One caveat on `tokio::fs`: it is not true async I/O. Most operating systems have no async file API, so tokio runs ordinary blocking `std::fs` operations on the `spawn_blocking` pool behind the scenes. That keeps the runtime thread unblocked, but every call carries `spawn_blocking` overhead - for many small reads it can be far slower than plain blocking I/O. Batch file work: read a whole file in one call, or do a sequence of filesystem operations inside a single `spawn_blocking`, rather than issuing hundreds of separate `tokio::fs` calls.

## Concurrency: `select!`, `join!`, `try_join!`

Run multiple futures concurrently in the same task.

```rust
use tokio::{join, try_join, select};

// Run both, wait for both
let (a, b) = join!(fetch_user(1), fetch_user(2));

// Run both, wait for both, short-circuit on error
let (a, b) = try_join!(fetch_user(1), fetch_user(2))?;

// Run both, take whichever finishes first
select! {
    a = fetch_user(1) => println!("got {a:?}"),
    _ = tokio::time::sleep(Duration::from_secs(5)) => println!("timeout"),
}
```

For dynamic-sized concurrency, use `futures::future::join_all` or `tokio::task::JoinSet`:

```rust
use tokio::task::JoinSet;

let mut set = JoinSet::new();
for id in 0..100 {
    set.spawn(fetch_user(id));
}
while let Some(res) = set.join_next().await {
    println!("{:?}", res?);
}
```

## Cancellation

Dropping a future cancels it. The future stops being polled at its next `.await` point. There is no "cancellation token" by default; structuring code so that dropping is a clean shutdown is the idiom.

For explicit cancellation across many tasks: `tokio_util::sync::CancellationToken`. For timeouts: `tokio::time::timeout`:

```rust
use tokio::time::{timeout, Duration};

match timeout(Duration::from_secs(5), slow_op()).await {
    Ok(Ok(value)) => { /* success */ }
    Ok(Err(e)) => { /* slow_op returned Err */ }
    Err(_) => { /* timed out */ }
}
```

### Handle SIGTERM, not just Ctrl-C

Almost every shutdown snippet online awaits `tokio::signal::ctrl_c()` and stops there. That is SIGINT only. Docker, Kubernetes, and systemd all stop a process with **SIGTERM** first and SIGKILL after a grace period - so a `ctrl_c()`-only service is hard-killed on every ordinary deploy, mid-request, and you will never see it locally because Ctrl-C in your terminal works perfectly.

```rust
use tokio::signal::unix::{signal, SignalKind};

async fn shutdown_signal() {
    let mut term = signal(SignalKind::terminate()).expect("install SIGTERM handler");
    tokio::select! {
        _ = tokio::signal::ctrl_c() => {}
        _ = term.recv() => {}
    }
}
```

Two things that bite after you fix that. A server's `with_graceful_shutdown` waits for **all** connections to close, so one long-lived streaming connection (SSE, a websocket, a follow-style tail) holds shutdown open forever - cancel that stream's own token as well, and put a bounded `timeout` around the drain as a backstop. And check that the handler is actually installed in the shipped artifact: on Linux, `grep SigCgt /proc/<pid>/status` tells you which signals the process is catching, which is how you find out that the binary in the container is not the one you tested.

## Channels (`tokio::sync`)

| Channel | Use |
|---|---|
| `mpsc` | Many producers, one consumer (work queue, command bus) |
| `oneshot` | Single send, single receive (request/response) |
| `broadcast` | Many producers, many consumers (each receiver gets every message; lossy if slow) |
| `watch` | Many producers, many consumers (each receiver gets only the latest value) |

```rust
use tokio::sync::mpsc;

let (tx, mut rx) = mpsc::channel::<String>(32);

tokio::spawn(async move {
    while let Some(msg) = rx.recv().await {
        println!("got: {msg}");
    }
});

tx.send("hi".into()).await?;
```

## Async in Traits

Native async functions in traits stabilized in Rust 1.75. They work for cases that do not need `dyn Trait`:

```rust
trait Greeter {
    async fn greet(&self) -> String;
}
```

Limitations: an `async fn` in a trait cannot be used as `dyn Trait` directly without help. For that, the `async-trait` crate is still common:

```toml
async-trait = "0.1"
```

```rust
#[async_trait::async_trait]
pub trait Greeter {
    async fn greet(&self) -> String;
}
```

`async-trait` boxes the future, which costs an allocation per call but lets you use `dyn Greeter`. For most app code, this is fine. Library authors writing performance-critical traits often avoid `async-trait` and use the native form with `impl Future` returns.

## Common Pitfalls

1. **Forgetting `.await`**: returns a `Future` that does nothing.
2. **Holding a `std::sync::MutexGuard` across `.await`**: see above.
3. **Calling blocking I/O in an async function**: use `spawn_blocking` or the async equivalent (`tokio::fs`).
4. **Spawning tasks that borrow from the parent**: `tokio::spawn` requires `'static`. Move owned data in (often via `Arc::clone`).
5. **`select!` arms with side effects**: when one arm completes, the others are dropped (cancelled). Make sure that is safe for the operations involved.
6. **Forgetting that `async fn` returns immediately**: until you `.await` or `spawn`, no work happens.
7. **One giant `tokio::main` task with no concurrency**: if your `main` is awaiting things sequentially, you may not need async at all. Async pays off when you have concurrent I/O.
8. **Assuming `impl Stream` means the body streams.** The signature promises an incremental *type*, not incremental *behavior* - a function returning `impl Stream` can happily read an entire file into a `String`, parse every record into a `Vec`, and only then yield item one. Nothing in the type system catches that. If a stream exists to bound memory, check that its body never materializes the whole input; the same trap hides inside `async_stream::stream!` blocks, where a plain `std::fs` call also blocks a runtime thread for the whole operation.

## Testing Time-Dependent Async Code

`tokio::time::pause` (and `#[tokio::test(start_paused = true)]`, which needs the `test-util` feature and the current-thread runtime) lets a test advance the clock instantly instead of sleeping. There is a precondition nobody mentions until it bites: **it can only control `tokio::time::Instant`, not `std::time::Instant`.** If your cache expiry, rate limiter, or backoff computes deadlines from `std::time::Instant::now()`, a paused test has no effect on it and you are back to real sleeps.

The fix is in the *production* code, not the test: use `tokio::time::Instant` there. Outside a paused runtime it is `std::time::Instant::now()`, so behavior is identical - you are only buying testability. Inside the test, advance explicitly with `tokio::time::advance()` rather than `sleep`, because a paused runtime auto-advances whenever it goes idle and a `sleep` will not mean what you think it means.

## Debugging a Running Runtime

When a service is stalling and the profiler shows nothing hot, the problem is usually a task that is not being polled rather than one burning CPU. `tokio-console` is the debugger for exactly that: it attaches over a `tracing` subscriber and shows live per-task state, poll counts, busy versus idle time, and warnings for tasks that have blocked the runtime. It needs the `tokio_unstable` cfg flag set at build time, which is why it is a deliberate step rather than something you leave on.

## What to Defer

- Manual `Future` impls and `Pin`. Almost no app code needs this.
- `poll_*` methods on lower-level traits (`AsyncRead`, `AsyncWrite`).
- Custom executors. Use `tokio` until you have a proven reason not to.
- `tokio` internals (`tokio-uring`, `LocalSet`, custom schedulers). Only relevant for advanced cases.
