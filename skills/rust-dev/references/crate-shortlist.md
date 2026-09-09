# Crate Shortlist

The handful of crates that show up in almost every Rust application. One minimal example each. None are required; pull in as you need them.

For a curated wider catalog, see [blessed.rs](https://blessed.rs/crates).

## `serde` and `serde_json`

Serialization. Derive macros do everything.

```toml
serde = { version = "1", features = ["derive"] }
serde_json = "1"
```

```rust
use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
struct User {
    id: u64,
    email: String,
}

let json = r#"{"id": 1, "email": "a@b.com"}"#;
let user: User = serde_json::from_str(json)?;

let back = serde_json::to_string_pretty(&user)?;
```

Other formats: `toml`, `serde_qs`, `rmp-serde` (MessagePack). Same derive, different crate.

Two names you will find in older guides that you should not reach for now:

- **`serde_yaml` is unmaintained.** Its repository is archived and the last release is `0.9.34+deprecated` (March 2024), with no official successor named. `serde_yaml_ng` and `serde_yml` are community continuations; evaluate them rather than assuming.
- **`bincode` 3.0.0 is a tombstone.** Development stopped after a doxxing and harassment incident, and the entire contents of 3.0.0's `src/lib.rs` is `compile_error!("https://xkcd.com/2347/")` - so adding `bincode = "3"` does not fail at runtime, it fails to compile. `2.0.1` is the last usable release. For a new binary format, upstream points at `postcard` or `rkyv`.

Common attributes:
```rust
#[derive(Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]   // userId on the wire, user_id in Rust
struct Payload {
    user_id: u64,

    #[serde(default)]                // missing field uses Default::default()
    tags: Vec<String>,

    #[serde(skip_serializing_if = "Option::is_none")]
    note: Option<String>,
}
```

## `tokio`

Async runtime. The default. See `async-basics.md` for the deep dive.

```toml
tokio = { version = "1", features = ["full"] }
```

```rust
#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let sleep = tokio::time::sleep(std::time::Duration::from_millis(100));
    sleep.await;
    Ok(())
}
```

## `anyhow`

App error handling. Use this in binaries.

```toml
anyhow = "1"
```

```rust
use anyhow::{Context, Result, bail};

fn run() -> Result<()> {
    let cfg = std::fs::read("config.toml").context("reading config.toml")?;
    if cfg.is_empty() {
        bail!("config is empty");
    }
    Ok(())
}
```

## `thiserror`

Library error enums.

```toml
thiserror = "2"
```

```rust
use thiserror::Error;

#[derive(Debug, Error)]
pub enum LoadError {
    #[error("not found: {0}")]
    NotFound(String),

    #[error("io error")]
    Io(#[from] std::io::Error),
}
```

## `clap`

CLI argument parsing. Derive-based; you write a struct, you have a CLI.

```toml
clap = { version = "4", features = ["derive"] }
```

```rust
use clap::Parser;

#[derive(Parser, Debug)]
#[command(version, about = "A widget tool")]
struct Args {
    /// Path to the input file
    input: std::path::PathBuf,

    /// Verbose output
    #[arg(short, long)]
    verbose: bool,

    /// Number of widgets to make
    #[arg(short, long, default_value_t = 1)]
    count: u32,
}

fn main() {
    let args = Args::parse();
    println!("{args:?}");
}
```

Subcommands:

```rust
#[derive(Parser)]
struct Cli {
    #[command(subcommand)]
    cmd: Cmd,
}

#[derive(clap::Subcommand)]
enum Cmd {
    Add { path: String },
    Remove { path: String },
}
```

**Two footguns that only show up once real users touch the binary.**

A positional argument beginning with `-` is parsed as a flag, so any command that forwards user-supplied text needs `--` in front of it. The failure rate is low enough to survive testing and high enough to hit production - a prompt, a search query, or a filename that happens to start with a dash:

```rust
// Shelling out to your own (or any) CLI with text you did not write:
// without the "--", a query like "- why does this fail" is read as flags.
std::process::Command::new("mytool")
    .arg("search")
    .arg("--")
    .arg(user_query);
```

On the receiving side, clap already stops parsing at `--`, so a positional declared with `#[arg(trailing_var_arg = true)]` or simply documented as "put `--` first" is what makes your own tool safe to call that way.

And **Rust ignores SIGPIPE at startup**, which the standard library says plainly: "we set SIGPIPE to ignore when the program starts up in order to prevent this problem." The consequence is that `mytool | head -5` does not exit quietly when `head` closes the pipe - your writes start returning `EPIPE`, and the panic or error surfaces from wherever you happened to be printing. Every Unix CLI a user pipes into `head`, `less`, or `grep -q` hits this. On stable, restore the default at the top of `main`:

```rust
// Cargo.toml: libc = "0.2"
fn main() {
    // SAFETY: restoring the OS default disposition before any threads exist.
    unsafe { libc::signal(libc::SIGPIPE, libc::SIG_DFL) };
    // ... clap parsing, the rest of main
}
```

(The nightly-only `-Zon-broken-pipe` flag does the same thing without `libc`; there is no stable flag equivalent yet.)

## `reqwest`

HTTP client. Async by default; the `blocking` feature gives a sync API.

```toml
reqwest = { version = "0.13", features = ["json"] }
```

```rust
#[derive(serde::Deserialize)]
struct Repo {
    full_name: String,
    stargazers_count: u32,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let client = reqwest::Client::builder()
        .user_agent("my-app/0.1")
        .build()?;

    let repo: Repo = client
        .get("https://api.github.com/repos/rust-lang/rust")
        .send()
        .await?
        .json()
        .await?;

    println!("{}: {} stars", repo.full_name, repo.stargazers_count);
    Ok(())
}
```

**0.13 notes** (if you find a 0.12 tutorial): `rustls` is now the default TLS backend (was `native-tls`), and the `rustls-tls` feature is renamed to `rustls`; `query` and `form` are now opt-in crate features. The `json` example above is unaffected.

Three more 0.13 changes that alter what you actually link, not just what you type. The rustls crypto provider "defaults to aws-lc instead of _ring_" - a different native dependency in your tree, and `rustls-no-provider` exists if you need to choose another. The rustls roots features were removed in favour of `rustls-platform-verifier`, so certificate validation now goes through the OS trust store by default rather than a bundled root set. And `native-tls` now includes ALPN, with `native-tls-no-alpn` to turn it back off.

For tiny sync tools where you do not want a tokio dep, `ureq` is the lightweight alternative.

## `tracing` and `tracing-subscriber`

Structured logging. The default in 2026 for any async code (replaces `log`).

```toml
tracing = "0.1"
tracing-subscriber = { version = "0.3", features = ["env-filter"] }
```

```rust
use tracing::{info, warn, error, instrument};
use tracing_subscriber::EnvFilter;

#[instrument]                                              // logs entry/exit
async fn handle(user_id: u64) -> anyhow::Result<()> {
    info!(user_id, "handling user");
    if user_id == 0 {
        warn!("got zero user");
    }
    Ok(())
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    tracing_subscriber::fmt()
        .with_env_filter(EnvFilter::from_default_env())   // RUST_LOG=info
        .init();

    handle(1).await?;
    Ok(())
}
```

Run with `RUST_LOG=info cargo run`. Use `error!`, `warn!`, `info!`, `debug!`, `trace!`. Add structured fields by passing them as named args: `info!(user_id, action = "create", "user created")`.

**The default writer is stdout, and that is a real hazard.** `SubscriberBuilder`'s writer type parameter defaults to `fn() -> Stdout`, with no TTY detection - so the example above interleaves log lines into stdout. For a service that is merely untidy. For any binary whose **stdout carries data** - a JSON-RPC or MCP server, a CLI that pipes records into another process, anything with a machine-readable stdout contract - it silently corrupts the output stream, and the failure looks like a protocol bug rather than a logging one. Logs belong on stderr; make it explicit:

```rust
tracing_subscriber::fmt()
    .with_writer(std::io::stderr)          // never inherit the stdout default
    .with_env_filter(EnvFilter::from_default_env())
    .init();
```

Two more you will want in production and not before: the `json` feature swaps in `format::Json`, "newline-delimited JSON logs... intended for production use", which is what a log aggregator wants instead of the human-readable default; and `tracing-appender` provides file appenders plus a non-blocking writer so a slow sink cannot stall the code that logged.

## `axum`

Web framework. Built on `tokio` + `hyper` + `tower`. The 2026 default.

```toml
axum = "0.8"
tokio = { version = "1", features = ["full"] }
```

```rust
use axum::{routing::get, Router, Json};
use serde::Serialize;

#[derive(Serialize)]
struct Health { ok: bool }

async fn root() -> &'static str {
    "hello"
}

async fn health() -> Json<Health> {
    Json(Health { ok: true })
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let app = Router::new()
        .route("/", get(root))
        .route("/health", get(health))
        .route("/users/{id}", get(|axum::extract::Path(id): axum::extract::Path<u64>| async move { format!("user {id}") }));

    let listener = tokio::net::TcpListener::bind("0.0.0.0:3000").await?;
    axum::serve(listener, app).await?;
    Ok(())
}
```

Path params, query params, JSON body, state, middleware all extract via the `FromRequest`/`FromRequestParts` traits. The axum docs are excellent.

**Scope middleware to the routes it exists for.** A `.layer(...)` attached to the whole `Router` runs on every route, which is fine for tracing and wrong for almost anything with a budget. A rate limiter meant to protect one expensive endpoint, hung on the root router, puts your static assets and health checks in the same bucket - and the first page load exhausts it. Layer the sub-router instead, and merge:

```rust
let expensive = Router::new()
    .route("/search", get(search))
    .layer(RateLimitLayer::new(5, Duration::from_secs(1)));

let app = Router::new()
    .route("/health", get(health))       // no rate limit
    .merge(expensive)
    .layer(TraceLayer::new_for_http());  // this one genuinely is global
```

**0.8 breaking changes** (if you find a 0.7 tutorial): path captures use `/{id}` and `/{*rest}` instead of `/:id` and `/*rest`; `Option<T>` extractors require the new `OptionalFromRequestParts` trait; `Host` extractor moved to `axum-extra`; WebSocket `Message` uses `Bytes`/`Utf8Bytes` instead of `Vec<u8>`/`String`. MSRV is 1.80 (raised in 0.8.9).

## `sqlx`

Async SQL with compile-time-checked queries. Postgres, MySQL, SQLite.

```toml
sqlx = { version = "0.9", features = ["runtime-tokio", "postgres", "macros", "migrate"] }
```

```rust
use sqlx::PgPool;

#[derive(sqlx::FromRow)]
struct User {
    id: i64,
    email: String,
}

async fn find_user(pool: &PgPool, id: i64) -> sqlx::Result<Option<User>> {
    sqlx::query_as!(
        User,
        "SELECT id, email FROM users WHERE id = $1",
        id
    )
    .fetch_optional(pool)
    .await
}
```

The `query_as!` macro connects to your dev database at compile time to verify the SQL and types. To work offline (CI without a DB), run `cargo sqlx prepare` and commit the generated `.sqlx/` directory. (sqlx 0.6+ replaced the single `sqlx-data.json` file with this directory; older guides may still reference the old path.)

For multi-crate workspaces, run `cargo sqlx prepare --workspace` to produce a single `.sqlx/` at the workspace root. In CI, `cargo sqlx prepare --check` exits non-zero when stored metadata is stale. To force offline mode without the CLI, set `SQLX_OFFLINE=true`.

Migrations: `sqlx migrate add init`, write SQL, `sqlx migrate run`.

**0.9 notes** (0.9.0 released 2026-05-21): the repository moved to the `transact-rs` GitHub org, and MSRV is now 1.94. The runtime `query()`/`query_as()` functions now take `impl SqlSafeStr` - wrap a dynamically built query string in `AssertSqlSafe(...)`. The `query_as!` macro shown above is unaffected (it takes a string literal). Older 0.8 tutorials otherwise still apply.

0.9 also added a per-crate `sqlx.toml`, which is where migration and macro settings now live instead of scattered environment variables. One packaging regression to know before you copy a CI recipe: upstream states "`cargo install --locked sqlx-cli` will no longer work", so install the CLI without `--locked`.

## `chrono` (and `jiff`)

Dates and times. As of Jan 2026 the chrono maintainer announced soft-deprecation and recommends `jiff` (BurntSushi) for new code. Reality in September 2026:

- `chrono` 0.4 is still production-safe and integrates cleanly with `serde`, `sqlx`, `serde_json`, and the rest of the ecosystem. Note the deprecation notice lives in the maintainer's issue thread, not in chrono's README, so the crate page looks entirely healthy.
- `jiff` is the recommended successor, but still pre-1.0 (0.2.35 as of September 2026, with the 1.0 tracking issue open), and its author says plainly: "I don't currently have a timeline for a Jiff 1.0 release." Migration across the ecosystem is partial rather than done - kube-rs and k8s-openapi have landed, while the arrow-rs and jj-vcs changes are still open PRs.
- Two things that lower the risk of picking `jiff` now: `jiff-sqlx` tracks sqlx 0.9, and `jiff-chrono-conversions` gives you `ToJiff`/`ToChrono` traits so a codebase can hold both during a migration. jiff also commits to critical bug fixes on 0.2 for a year after 1.0 ships.

Pick `chrono` if you need ecosystem integration today. Pick `jiff` for new code that can tolerate pre-1.0 churn and where you want correct timezone-aware arithmetic out of the box.

```toml
chrono = { version = "0.4", features = ["serde"] }
# or
jiff   = { version = "0.2", features = ["serde"] }
```

```rust
// chrono
use chrono::{DateTime, Utc};

let now: DateTime<Utc> = Utc::now();
let parsed: DateTime<Utc> = "2026-04-29T12:00:00Z".parse()?;
let in_an_hour = now + chrono::Duration::hours(1);

// jiff (equivalent)
use jiff::{Timestamp, ToSpan};

let now: Timestamp = Timestamp::now();
let parsed: Timestamp = "2026-04-29T12:00:00Z".parse()?;
let in_an_hour = now + 1.hour();
```

## When `anyhow` + `thiserror` Is Not Enough

The app/library split covers almost everything, and you should not go shopping before you have a concrete complaint. When you do, these are the four alternatives worth knowing and what each actually buys:

| Crate | Reach for it when |
|---|---|
| `eyre` | You want `anyhow`'s ergonomics but control over how reports are *rendered* - it is a fork of anyhow built around customizable error reports, usually paired with `color-eyre` for readable panics and backtraces in a binary |
| `miette` | Your errors point at a span of user input - a parser, a config file, a query language. It renders rustc-style diagnostics with source snippets and carets. (This is what `dist` itself uses.) |
| `snafu` | You want typed error enums like `thiserror`, but with context selectors that attach data at each `?` site instead of only at the boundary |
| `error-stack` | You want an attachable, inspectable context *stack* rather than a flat chain - richer than anyhow's `.context()`, at the cost of a more opinionated API |

Do not migrate a working `anyhow`/`thiserror` codebase to any of these without a specific reason; the split in this skill is still the default.

## Honorable Mentions

Not on the day-1 list, but you will run into these:

| Crate | Use |
|---|---|
| `rayon` | Parallel iterators. `par_iter()` on a `Vec` and your CPU cores light up |
| `regex` | Regular expressions |
| `uuid` | UUID generation and parsing |
| `dotenvy` | Load `.env` into environment variables |
| `config` | Layered config (file + env + CLI) |
| `bytes` | Efficient byte buffer handling |
| `futures` | Future combinators not in `std` |
| `parking_lot` | Faster `Mutex`/`RwLock` than `std::sync` (in some workloads) |
| `dashmap` | Concurrent hashmap |
| `indexmap` | Hashmap that preserves insertion order |
| `once_cell` / `LazyLock` (std 1.80+) | Lazy global initialization |
| `crossbeam-channel` | Multi-producer, multi-consumer sync channels |
| `tower` | Service abstraction (used by axum middleware) |
| `tonic` | gRPC |
| `redis` | Redis client |
| `mongodb` | MongoDB driver |
