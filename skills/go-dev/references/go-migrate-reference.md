# golang-migrate Reference

Latest: **v4.19.1** (November 2025). Supports Go 1.24 and 1.25. MIT license, 18K+ stars.

## Installation

### CLI

```bash
# Homebrew (macOS)
brew install golang-migrate

# Scoop (Windows)
scoop install migrate

# Pre-built binary
curl -L https://github.com/golang-migrate/migrate/releases/download/v4.19.1/migrate.linux-amd64.tar.gz | tar xvz

# With Go (specify database driver via build tags)
go install -tags 'postgres' github.com/golang-migrate/migrate/v4/cmd/migrate@v4.19.1

# Docker
docker run -v $(pwd)/migrations:/migrations --network host migrate/migrate \
    -path=/migrations/ -database "postgres://localhost:5432/db" up
```

Multiple drivers: `-tags 'postgres mysql sqlite3'`

### Library

```bash
go get github.com/golang-migrate/migrate/v4
```

## Migration File Naming

Format: `{version}_{title}.{direction}.sql`

### Sequential (recommended for smaller teams)

```bash
migrate create -ext sql -dir migrations -seq create_users_table
```

Produces:
```
migrations/
  000001_create_users_table.up.sql
  000001_create_users_table.down.sql
```

Control zero-padding with `-digits N` (default: 6).

### Timestamp (better for larger teams)

```bash
migrate create -ext sql -dir migrations create_users_table
```

Produces:
```
migrations/
  1712345678_create_users_table.up.sql
  1712345678_create_users_table.down.sql
```

Eliminates version conflicts when multiple developers create migrations simultaneously.

## CLI Commands

```bash
# Apply all pending migrations
migrate -path migrations -database "$DATABASE_URL" up

# Apply next N migrations
migrate -path migrations -database "$DATABASE_URL" up 2

# Revert last N migrations
migrate -path migrations -database "$DATABASE_URL" down 1

# Revert ALL (interactive confirmation)
migrate -path migrations -database "$DATABASE_URL" down

# Revert all without confirmation
migrate -path migrations -database "$DATABASE_URL" down -all

# Check current version
migrate -path migrations -database "$DATABASE_URL" version

# Migrate to specific version (up or down)
migrate -path migrations -database "$DATABASE_URL" goto 3

# Fix dirty database state (set version without running migration)
migrate -path migrations -database "$DATABASE_URL" force 2

# Drop everything (dangerous)
migrate -path migrations -database "$DATABASE_URL" drop -f

# Create new migration files
migrate create -ext sql -dir migrations -seq add_email_column
```

**CLI options:**
- `-source` - migration source (driver://url)
- `-path` - shorthand for `-source=file://path`
- `-database` - database connection URL
- `-prefetch N` - migrations to load ahead (default 10)
- `-lock-timeout N` - seconds to acquire lock (default 15)
- `-verbose` - verbose logging

Handles `SIGINT` gracefully, stopping at a safe point.

## Up/Down Migration Patterns

**Up migration** (`000001_create_users.up.sql`):
```sql
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    email       VARCHAR(255) UNIQUE NOT NULL,
    name        VARCHAR(100) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users (email);
```

**Down migration** (`000001_create_users.down.sql`):
```sql
DROP TABLE IF EXISTS users;
```

**Multi-statement with transaction** (`000002_add_status.up.sql`):
```sql
BEGIN;

CREATE TYPE user_status AS ENUM ('active', 'inactive', 'banned');
ALTER TABLE users ADD COLUMN status user_status NOT NULL DEFAULT 'active';

COMMIT;
```

**Down** (`000002_add_status.down.sql`):
```sql
BEGIN;

ALTER TABLE users DROP COLUMN status;
DROP TYPE user_status;

COMMIT;
```

## Library Usage

### Basic (URL-based)

```go
import (
    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

m, err := migrate.New(
    "file://migrations",
    "postgres://user:pass@localhost:5432/mydb?sslmode=disable")
if err != nil {
    log.Fatal(err)
}

if err := m.Up(); err != nil && err != migrate.ErrNoChange {
    log.Fatal(err)
}
```

### With Existing Connection

```go
import (
    "database/sql"
    "github.com/golang-migrate/migrate/v4"
    "github.com/golang-migrate/migrate/v4/database/postgres"
    _ "github.com/golang-migrate/migrate/v4/source/file"
)

db, _ := sql.Open("postgres", connStr)
driver, _ := postgres.WithInstance(db, &postgres.Config{})
m, _ := migrate.NewWithDatabaseInstance("file://migrations", "postgres", driver)

m.Up()        // Apply all pending
m.Steps(2)    // Apply 2 up
m.Steps(-1)   // Revert 1
m.Version()   // Get current version + dirty flag
m.Force(3)    // Set version without running
m.Close()     // Close connections
```

Always check for `migrate.ErrNoChange` when calling `Up()` - it means no new migrations exist and is not a real error.

## Embedding Migrations with embed.FS

Produce self-contained binaries by embedding migrations at compile time:

```go
package main

import (
    "embed"
    "log"

    "github.com/golang-migrate/migrate/v4"
    _ "github.com/golang-migrate/migrate/v4/database/postgres"
    "github.com/golang-migrate/migrate/v4/source/iofs"
)

//go:embed migrations/*.sql
var migrationsFS embed.FS

func runMigrations(databaseURL string) error {
    d, err := iofs.New(migrationsFS, "migrations")
    if err != nil {
        return err
    }

    m, err := migrate.NewWithSourceInstance("iofs", d, databaseURL)
    if err != nil {
        return err
    }

    if err := m.Up(); err != nil && err != migrate.ErrNoChange {
        return err
    }

    return nil
}
```

The `//go:embed` directive path is relative to the Go source file containing it.

## PostgreSQL-Specific

URL format: `postgres://user:password@host:port/dbname?query`

| Parameter | Description |
|-----------|-------------|
| `x-migrations-table` | Custom migrations table name (default: `schema_migrations`) |
| `x-statement-timeout` | Abort statements exceeding N ms |
| `x-multi-statement` | Enable multi-statement execution (default: false) |
| `x-multi-statement-max-size` | Max statement size in bytes (default: 10MB) |
| `search_path` | Schema search path |
| `sslmode` | disable, require, verify-ca, verify-full |

Uses `pg_advisory_lock` for safe concurrent migrations.

## Transaction Handling

golang-migrate does **NOT** automatically wrap migrations in transactions. You must use explicit `BEGIN`/`COMMIT`:

```sql
BEGIN;
ALTER TABLE users ADD COLUMN phone VARCHAR(20);
CREATE INDEX idx_users_phone ON users (phone);
COMMIT;
```

**Exception:** `CREATE INDEX CONCURRENTLY` cannot run inside a transaction. Put it in its own migration file without `BEGIN`/`COMMIT`:

```sql
-- 000003_add_concurrent_index.up.sql
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_users_name ON users (name);
```

## Dirty Database State

When a migration fails mid-execution, the database is marked "dirty" and no further migrations run.

To recover:
1. Check current state: `migrate version` (shows version + dirty flag)
2. Fix the issue manually in the database
3. Force the correct version: `migrate force <version>`

If the failed migration partially applied, you may need to manually undo the partial changes before forcing.

## Supported Databases

PostgreSQL, PGX v4/v5, MySQL/MariaDB, SQLite, MS SQL Server, MongoDB, CockroachDB, YugabyteDB, ClickHouse, Cassandra/ScyllaDB, Neo4j, Cloud Spanner, Redshift, and more.

## Migration Sources

Filesystem, `embed.FS` (iofs), GitHub, GitLab, Bitbucket, AWS S3, Google Cloud Storage.

## CI/CD Patterns

### Test Migrations (up-down-up) in CI

```yaml
services:
  postgres:
    image: postgres:17
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: testdb
    ports: ["5432:5432"]
steps:
  - name: Run migrations up
    run: migrate -path migrations -database "postgresql://test:test@localhost:5432/testdb?sslmode=disable" up
  - name: Run migrations down
    run: migrate -path migrations -database "postgresql://test:test@localhost:5432/testdb?sslmode=disable" down -all
  - name: Run migrations up again
    run: migrate -path migrations -database "postgresql://test:test@localhost:5432/testdb?sslmode=disable" up
```

The up-down-up pattern validates both directions work correctly.

## Common Pitfalls

1. **Dirty state after failure** - most common issue. Must `force` correct version after manual fix
2. **Version conflicts in teams** - use timestamp versioning for larger teams
3. **Missing down migrations** - always write both directions, even if down is a no-op (add a SQL comment)
4. **Non-transactional DDL** - `CREATE INDEX CONCURRENTLY` needs its own migration without `BEGIN`/`COMMIT`
5. **URL encoding** - special characters in passwords must be percent-encoded
6. **Empty files** - 0-byte migration files cause issues. Add a SQL comment if intentionally empty
7. **Schema + role name clash** in PostgreSQL - `search_path` causes migrations table duplication. Fix: set `search_path=public` in URL
8. **Never edit applied migrations** - treat merged migrations as immutable. Create new ones for corrections

## Best Practices

- Keep migrations small and focused - one logical change per migration
- Always test up-down-up before merging
- Use transactions for multi-statement migrations (when database supports it)
- Embed migrations for production binaries (`embed.FS` + `iofs`)
- Run migrations at app startup or as a separate step in the deploy pipeline
- Use `migrate.ErrNoChange` check in programmatic usage
- Pin `migrate` CLI version in CI for reproducibility
