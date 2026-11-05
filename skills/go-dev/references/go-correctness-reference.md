# Go Correctness Reference

Bug classes that kept recurring in code review of real Go services and CLIs. The linters in SKILL.md catch none of them reliably. Each entry is the failure, then the fix. Verified against go1.27.3.

## Filesystem Confinement

The most recurring security class: a user- or config-supplied name escapes the directory it was meant to stay in.

- **`filepath.Join` cleans `..`.** `filepath.Join("/base", "../../etc")` is `/etc`, so a `--name ../../x` flag that feeds a `RemoveAll` deletes outside the base. Reject the name first with `filepath.IsLocal` (Go 1.20+), which is false for `../../etc`, absolute paths and, on Windows, reserved names.
- **Lexical checks do not stop symlinks.** `IsLocal` and prefix checks pass for `data/link` even when `link` points at the user's home. For operations inside a directory you do not fully control, use `os.Root` (Go 1.24+): every method resolves the name inside the root and fails if it - or any symlink along the way - escapes.
- **`os.Open` then `Stat()` follows links.** `f.Stat().Mode().IsRegular()` is true for a symlink to a regular file. Use `os.Lstat`, or open with `syscall.O_NOFOLLOW` on Unix.
- **Archive extraction must check link targets.** A tar entry's name can be local while its `hdr.Linkname` points anywhere; check both, or extract through an `os.Root`.
- **Compare directories by identity, not by string.** A guard that refuses to touch `$HOME` misses a symlink alias of it. Compare `os.Stat` results with `os.SameFile`.

```go
func purgeCache(base, name string) error {
    if !filepath.IsLocal(name) {
        return fmt.Errorf("invalid name %q", name)
    }
    root, err := os.OpenRoot(base)
    if err != nil {
        return fmt.Errorf("open root: %w", err)
    }
    defer root.Close()
    return root.RemoveAll(name) // cannot leave base, even through a swapped symlink
}
```

## Context Lifetimes

- **A request context must not own a long-lived resource.** A handler that starts a child process (or a background job) and passes `r.Context()` to its readiness wait lets a client's short timeout kill the freshly started child, which then restarts on the next poll and never stabilises. Detach and bound it: `context.WithTimeout(context.WithoutCancel(r.Context()), 30*time.Second)` keeps the request's values but not its cancellation. On the client side, a per-poll timeout shorter than the server's startup makes the same loop; size it to the remaining overall deadline.
- **Bound shutdown work.** Escaping a SIGTERM-cancelled context with `context.Background()` makes teardown unbounded, and the orchestrator then kills the process mid-cleanup. Derive the shutdown context with `WithoutCancel` plus a timeout that fits inside the grace period (`docker stop -t`, `terminationGracePeriodSeconds`), split across phases (HTTP drain, then children, then flush).
- **Saves that must outlive the caller** - a final state write after the caller gave up - get the same `WithTimeout(WithoutCancel(ctx), d)` treatment, not `Background()`.
- **Make cancellation outcomes explicit.** "Cancelled before the side effect was attempted" and "attempted, outcome unknown" need different handling, so return a sentinel that still wraps `context.Canceled` for the first, keeping `errors.Is(err, context.Canceled)` true while letting callers tell the cases apart.

```go
func runServer(srv *http.Server) error {
    ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
    defer stop()

    errc := make(chan error, 1)
    go func() { errc <- srv.ListenAndServe() }()

    select {
    case err := <-errc:
        return fmt.Errorf("serve: %w", err)
    case <-ctx.Done():
    }
    shutdownCtx, cancel := context.WithTimeout(context.WithoutCancel(ctx), 10*time.Second)
    defer cancel()
    if err := srv.Shutdown(shutdownCtx); err != nil {
        return fmt.Errorf("shutdown: %w", err)
    }
    return nil
}
```

## Child Processes

- **Signal the process group, not the PID.** A child that spawns its own children (a shell, ssh, a browser) leaves them running when only its PID is killed. Start it in its own group and signal the negative PID:

```go
//go:build unix

func startGroup(ctx context.Context, name string, args ...string) (*exec.Cmd, error) {
    cmd := exec.CommandContext(ctx, name, args...)
    cmd.SysProcAttr = &syscall.SysProcAttr{Setpgid: true}
    cmd.Cancel = func() error { return syscall.Kill(-cmd.Process.Pid, syscall.SIGTERM) }
    cmd.WaitDelay = 5 * time.Second // then SIGKILL the child and close pipes
    if err := cmd.Start(); err != nil {
        return nil, fmt.Errorf("start %s: %w", name, err)
    }
    return cmd, nil
}
```

- **Kill the child if a post-start step fails.** If writing the pidfile or state after `cmd.Start()` fails and the function returns the error, the child keeps running as an orphan nobody tracks.
- **Never write `_ = cmd.Wait()`.** The error carries the exit status and the signal; discard it and the logs can never distinguish a crash from a deliberate kill. Inspect it with `errors.As(err, &exitErr)` and, on Unix, `exitErr.Sys().(syscall.WaitStatus).Signaled()`.
- **Match argv by token, not substring.** `strings.Contains(cmdline, dir)` matches instance `a` against instance `ab`'s arguments. Compare the exact `--flag=value` token.

## Timers and Concurrency

- **`time.AfterFunc`'s `Stop()` can lose the race.** "if t.Stop returns false, then the timer has already expired and the function f has been started in its own goroutine". In a TTL map whose callback deletes the entry under the map's mutex, a replacement `put` that ignores `Stop()`'s result is then wiped by the old callback. Store a generation number (or the timer pointer) with the entry and have the callback delete only if it still matches.
- **`sync.Mutex` is not reentrant.** A method that holds `mu` and calls a helper that also locks `mu` deadlocks. Split helpers into a locked wrapper and an `...Locked` body.
- **No blocking work under a hot mutex.** Synchronous `slog` output to stderr, database queries and persistence inside a critical section stall every health check, metric scrape and broadcast behind them. Collect what you need under the lock, unlock, then log or write.
- **Re-check gates under the lock.** A condition checked before taking the mutex can change before you hold it (check-then-act). Check again after locking.
- **Whole-struct write-back loses updates.** Goroutines that each read a shared record, change one field and write the whole struct back are last-writer-wins: concurrent updates to other fields vanish, and the race detector catches only some variants. Mutate under a mutex on a clone and merge field by field, or update single columns.
- **A boolean "busy, skip" guard is not a lock.** Shutdown that sees `busy == true` and skips waits for nothing and kills the in-flight work. Use a mutex (or a `sync.WaitGroup`) so teardown waits.
- **Per-request goroutines leak.** A handler that spawns a goroutine to try-lock with a timeout leaks one goroutine per request for as long as the lock is held. Share one prober goroutine and read its last result.
- **A `recover` fallback can panic again.** A writer goroutine that recovers from a logger panic and then logs the failure through the same logger panics a second time and dies. Guard the fallback too, and test repeated panics, not only the first.

## Strings, Encoding and Errors

- **`strings.ToLower` changes byte length.** `len("İ")` is 2 and `len(strings.ToLower("İ"))` is 1, so a byte offset found in a lowercased copy and used to slice the original can point into a rune or past the end - a remotely triggerable panic in any handler that searches user text. Search with `strings.Index` on case-folded runes, or keep offsets in the string you slice.
- **`encoding/json` drops unknown fields.** A peer on the previous version decodes a message, loses fields it does not know, and re-encodes it without them. Making a new field mandatory therefore breaks a mixed-version rollout; keep it optional for one release, or negotiate the capability.
- **`URL.Redacted()` needs a parsed user.** `url.Parse("user:secret@db.example:5432")` succeeds with scheme `user` and no `User`, so `Redacted()` returns the password verbatim. Normalise the scheme before parsing, and log only `scheme://host:port`, falling back to `<redacted>` when parsing fails.
- **A masking `slog.Handler` must implement `WithAttrs` and `WithGroup`.** A wrapper that only filters in `Handle` is bypassed by every attribute bound earlier with `logger.With(...)`.
- **Overflow-safe size guards divide.** To cap the output of a replace-all style expansion, check `count > limit/len(replacement)` rather than `count*len(replacement) > limit`, which can overflow.
- **Package variables initialise before `init()`.** Initialisers run first, then `init()` functions, file by file in the order the go command presents them (sorted by file name). A value "fixed up" in `init()` is too late for anything built in a variable initialiser.

## CLIs and HTTP

- **An empty flag value is not "use the default" on destructive verbs.** An unset shell variable turned `--name "$NAME"` into `--name ""`, which fell through to the default instance and purged its data. Reject empty values (with cobra, `cmd.Flags().Changed("name")` tells set-but-empty from unset), and run preflight checks such as an image pull or port check before tearing anything down.
- **Framework middleware wraps only framework routes.** A route mounted directly on the underlying `http.ServeMux` or router, beneath a framework that registers its own operations, skips the framework's middleware chain - authentication included. Mount everything through one path, and test that unauthenticated requests to every route are refused.
- **One Prometheus `Collector` per scrape.** A `GaugeFunc` per metric whose callback locks and recomputes the full snapshot multiplies scrape cost by the number of metrics. Implement one `prometheus.Collector` that snapshots once in `Collect` and emits all of them.

## database/sql and SQLite

- **`SetMaxOpenConns(1)` serialises reads behind writes.** It is the usual way to make SQLite writes safe, but every read then queues behind every write transaction (one 400-row write blocked a read for 572ms; the same read on its own read-only connection took 37us). Open two pools on the same file: one writer with `SetMaxOpenConns(1)`, and a small read-only pool (`mode=ro`, WAL journal mode). A `sql.Tx` already pins its own connection.
- **Context deadlines may not stop a running SQLite query.** With `modernc.org/sqlite` v1.57, a 300ms deadline bounded only the wait for the first row; the query then ran for 20s. SQLite's progress handler (`sqlite3_progress_handler`, exposed by the drivers) interrupts long statements reliably. Probe your own driver version before relying on cancellation.
- **`PRAGMA query_only` is not a security boundary.** Caller-supplied SQL can run `PRAGMA query_only=0`, and `VACUUM INTO` or `ATTACH` can copy the whole database to any path. Untrusted SQL needs an authorizer callback with an allowlist.
- **Optional-filter queries defeat indexes.** The convenient `WHERE (? IS NULL OR col = ?)` shape prevents an index lookup even when the parameter is set (13.3ms vs 0.3ms for a specialised query). Generate one query per filter combination that matters. sqlc's generated methods are not prepared statements unless `emit_prepared_queries` is set.
- **Fix query shape before swapping drivers.** The cgo SQLite driver measured 1.6-4x faster than the pure-Go one on identical SQL, but an index plus a correlated `EXISTS` took one endpoint from ~100ms to ~2ms on either driver.
