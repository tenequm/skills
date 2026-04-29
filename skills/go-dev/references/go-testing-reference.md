# Go Testing Reference

Covers Go testing best practices, patterns, and tooling as of Go 1.26 (2026).

## Table-Driven Tests

The idiomatic Go testing pattern. Use named struct slices with `t.Run()` for subtests:

```go
func TestUserValidation(t *testing.T) {
    tests := []struct {
        name    string
        user    User
        wantErr error
    }{
        {
            name:    "valid user",
            user:    User{Email: "[email protected]", Age: 25},
            wantErr: nil,
        },
        {
            name:    "missing email",
            user:    User{Age: 25},
            wantErr: ErrInvalidEmail,
        },
        {
            name:    "negative age",
            user:    User{Email: "[email protected]", Age: -1},
            wantErr: ErrInvalidAge,
        },
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            err := tt.user.Validate()
            if !errors.Is(err, tt.wantErr) {
                t.Errorf("Validate() error = %v, wantErr %v", err, tt.wantErr)
            }
        })
    }
}
```

**Note:** Since Go 1.22, the loop variable capture bug is fixed. `tt := tt` inside the loop is no longer needed, even with `t.Parallel()`.

## Parallel Tests

```go
func TestParallel(t *testing.T) {
    tests := []struct {
        name  string
        input int
        want  int
    }{
        {"double 1", 1, 2},
        {"double 5", 5, 10},
    }
    for _, tt := range tests {
        t.Run(tt.name, func(t *testing.T) {
            t.Parallel() // Safe without tt := tt in Go 1.22+
            got := Double(tt.input)
            if got != tt.want {
                t.Errorf("got %d, want %d", got, tt.want)
            }
        })
    }
}
```

Default parallelism = `GOMAXPROCS`. Override with `go test -parallel N`.

## Testing Helpers (Go 1.14-1.26)

### t.Helper()

Mark functions as test helpers so failures report the caller's line:

```go
func assertNoError(t testing.TB, err error) {
    t.Helper()
    if err != nil {
        t.Fatalf("unexpected error: %v", err)
    }
}
```

Use `testing.TB` as the parameter type so helpers work in both tests and benchmarks.

### t.Cleanup(func()) - Go 1.14

Register cleanup that runs after the test and all subtests complete. LIFO order:

```go
func newTestDB(t *testing.T) *DB {
    t.Helper()
    db := openDB()
    t.Cleanup(func() { db.Close() })
    return db
}
```

### t.TempDir() - Go 1.15

Auto-cleaned temporary directory:

```go
func TestWriteFile(t *testing.T) {
    dir := t.TempDir() // Removed automatically after test
    path := filepath.Join(dir, "output.txt")
    err := os.WriteFile(path, []byte("hello"), 0o644)
    require.NoError(t, err)
}
```

### t.Setenv(key, value) - Go 1.17

Set env var for test duration, restored on cleanup:

```go
func TestConfig(t *testing.T) {
    t.Setenv("DATABASE_URL", "postgres://test@localhost/testdb")
    cfg := LoadConfig()
    assert.Equal(t, "postgres://test@localhost/testdb", cfg.DatabaseURL)
}
```

Cannot be used with `t.Parallel()` (panics).

### t.Context() - Go 1.21

Returns a context cancelled when the test finishes:

```go
func TestWithContext(t *testing.T) {
    ctx := t.Context()
    result, err := service.Fetch(ctx, "key")
    require.NoError(t, err)
}
```

### t.ArtifactDir() - Go 1.26

Directory for test artifacts that persists after the test. Set the location with `-outputdir`; emit a manifest with `-artifacts`:

```go
func TestRender(t *testing.T) {
    dir := t.ArtifactDir()
    path := filepath.Join(dir, "output.html")
    os.WriteFile(path, rendered, 0o644)
}
```

Available as `T.ArtifactDir`, `B.ArtifactDir`, and `F.ArtifactDir`.

## Testify

Latest: **v1.10+**. The most popular assertion library. Four packages:

### assert (soft assertions - test continues)

```go
import "github.com/stretchr/testify/assert"

func TestUser(t *testing.T) {
    user := GetUser("123")
    assert.Equal(t, "alice", user.Name)
    assert.NotEmpty(t, user.ID)
    assert.NoError(t, user.Validate())
    assert.Contains(t, user.Email, "@")
    assert.Len(t, user.Roles, 2)
    assert.True(t, user.Active)
    assert.WithinDuration(t, time.Now(), user.CreatedAt, time.Minute)
}
```

### require (hard assertions - test stops on failure)

```go
import "github.com/stretchr/testify/require"

func TestFetch(t *testing.T) {
    result, err := Fetch("key")
    require.NoError(t, err)    // Stops here if error
    require.NotNil(t, result)  // Only runs if no error
    assert.Equal(t, "value", result.Data)
}
```

**Rule of thumb:** Use `require` for preconditions (error checks, nil checks), `assert` for the actual assertions.

### suite (setup/teardown lifecycle)

```go
import "github.com/stretchr/testify/suite"

type UserSuite struct {
    suite.Suite
    db *sql.DB
}

func (s *UserSuite) SetupSuite()    { s.db = connectTestDB() }
func (s *UserSuite) TearDownSuite() { s.db.Close() }
func (s *UserSuite) SetupTest()     { truncateAll(s.db) }

func (s *UserSuite) TestCreate() {
    err := CreateUser(s.db, "alice")
    s.NoError(err)
}

func TestUserSuite(t *testing.T) { suite.Run(t, new(UserSuite)) }
```

### mock (expectations)

```go
import "github.com/stretchr/testify/mock"

type MockRepo struct { mock.Mock }

func (m *MockRepo) Get(id string) (*User, error) {
    args := m.Called(id)
    return args.Get(0).(*User), args.Error(1)
}

func TestService(t *testing.T) {
    repo := new(MockRepo)
    repo.On("Get", "123").Return(&User{Name: "alice"}, nil)

    svc := NewService(repo)
    user, err := svc.FindUser("123")
    require.NoError(t, err)
    assert.Equal(t, "alice", user.Name)

    repo.AssertExpectations(t)
}
```

## Mock Libraries

| Library | Approach | Best For |
|---------|----------|----------|
| **go.uber.org/mock** (v0.6) | Code gen via `mockgen` | Precise expectations, call ordering |
| **vektra/mockery** (v3) | Batch code gen, templates | Large codebases (5-30x faster than sequential mockgen) |
| **matryer/moq** | Function-field based mocks | Lightweight, simple mocks |
| **testify/mock** | Runtime (no codegen) | Quick mocking without generators |
| **Hand-written** | Interface implementation | Full control, no dependencies |

### gomock (go.uber.org/mock)

```bash
go install go.uber.org/mock/mockgen@latest
```

```go
//go:generate mockgen -source=repository.go -destination=mock_repository.go -package=user

func TestWithGomock(t *testing.T) {
    ctrl := gomock.NewController(t)
    repo := NewMockRepository(ctrl)
    repo.EXPECT().Get("123").Return(&User{Name: "alice"}, nil)

    svc := NewService(repo)
    user, _ := svc.FindUser("123")
    assert.Equal(t, "alice", user.Name)
}
```

### mockery v3

Config-driven batch processing:

```yaml
# .mockery.yml
packages:
  github.com/yourorg/myapp/internal/user:
    interfaces:
      Repository:
      Service:
```

```bash
mockery  # Generates all mocks in one pass
```

## Benchmarks

### testing.B.Loop (Go 1.24+ - preferred)

```go
func BenchmarkSort(b *testing.B) {
    data := generateData() // Setup excluded automatically
    for b.Loop() {
        sort.Ints(data)
    }
    // No b.ResetTimer() needed - setup/cleanup excluded automatically
}
```

Benefits of `b.Loop()`:
- Automatically excludes setup/cleanup from timing
- Prevents dead-code elimination
- Benchmark function called only once (faster)

### Old pattern (still works)

```go
func BenchmarkSortOld(b *testing.B) {
    data := generateData()
    b.ResetTimer()
    for i := 0; i < b.N; i++ {
        sort.Ints(data)
    }
}
```

### Sub-benchmarks

```go
func BenchmarkCache(b *testing.B) {
    b.Run("Set", func(b *testing.B) { for b.Loop() { cache.Set("k", "v") } })
    b.Run("Get", func(b *testing.B) { for b.Loop() { cache.Get("k") } })
}
```

### Running and Comparing

```bash
go test -bench=. -benchmem ./...
go test -bench=. -benchmem -count=5 ./... > old.txt
# make changes
go test -bench=. -benchmem -count=5 ./... > new.txt
benchstat old.txt new.txt
```

Always use `-benchmem` - allocations per op often matter more than raw speed.

## Build Tags for Test Separation

Use `//go:build` (not the old `// +build`):

```go
//go:build integration

package user_test

func TestUserRepository_Integration(t *testing.T) {
    db := connectRealDB(t)
    // ...
}
```

Run: `go test -tags=integration ./...`

### Alternative: testing.Short()

```go
func TestSlow(t *testing.T) {
    if testing.Short() {
        t.Skip("skipping in short mode")
    }
    // expensive test
}
```

Run unit tests only: `go test -short ./...`

### Alternative: Custom Flags

```go
var integration = flag.Bool("integration", false, "run integration tests")

func TestMain(m *testing.M) {
    flag.Parse()
    os.Exit(m.Run())
}

func TestDB(t *testing.T) {
    if !*integration {
        t.Skip("pass -integration to run")
    }
}
```

Run: `go test -integration ./...`

## Coverage

```bash
go test -cover ./...                           # Summary
go test -coverprofile=coverage.out ./...        # Generate profile
go tool cover -html=coverage.out                # HTML report
go tool cover -func=coverage.out                # Function-level summary
go test -coverpkg=./... ./...                   # Cross-package coverage
```

**Coverage modes:**
- `-covermode=set` - did each statement run? (boolean)
- `-covermode=count` - how many times?
- `-covermode=atomic` - thread-safe count (use with `-race`)

**Integration test coverage** (Go 1.20+):

```bash
go build -cover -o myapp .
GOCOVERDIR=./coverage_data ./myapp
go tool covdata textfmt -i=./coverage_data -o coverage.out
```

## Race Detector

```bash
go test -race ./...
```

- Zero false positives - if it reports a race, it is real
- ~2-10x slower, ~5-10x more memory
- Only detects races on actually executed paths
- **Always use `-race` in CI** - the single most important testing flag
- Combine with `-count=N` for better detection

## Fuzz Testing

```go
func FuzzParse(f *testing.F) {
    // Seed corpus
    f.Add("valid input")
    f.Add("")
    f.Add("edge case")

    f.Fuzz(func(t *testing.T, input string) {
        result, err := Parse(input)
        if err != nil {
            return // Invalid input is fine
        }
        // Property: round-trip should preserve data
        encoded := result.String()
        result2, err := Parse(encoded)
        if err != nil {
            t.Errorf("round-trip failed: %v", err)
        }
        if !reflect.DeepEqual(result, result2) {
            t.Errorf("round-trip mismatch")
        }
    })
}
```

Run: `go test -fuzz=FuzzParse`

Seed corpus stored in `testdata/fuzz/<FuzzTestName>/` - commit to version control.

Best for: parsers, encoders/decoders, protocol implementations, user input handling.

## Golden File Testing

Compare output against a pre-approved reference file:

```go
var update = flag.Bool("update", false, "update golden files")

func TestRender(t *testing.T) {
    got := RenderTemplate(data)
    golden := filepath.Join("testdata", t.Name()+".golden")

    if *update {
        os.WriteFile(golden, []byte(got), 0o644)
        return
    }

    want, err := os.ReadFile(golden)
    require.NoError(t, err)
    if diff := cmp.Diff(string(want), got); diff != "" {
        t.Errorf("mismatch (-want +got):\n%s", diff)
    }
}
```

Update golden files: `go test -update ./...`

Libraries: `sebdah/goldie/v2`, `gotest.tools/v3/golden`

## testdata/ Convention

Go's toolchain ignores `testdata/` directories:

```
internal/user/
  user.go
  user_test.go
  testdata/
    valid_user.json
    invalid_user.json
    fuzz/FuzzParse/   # Fuzz corpus
```

Access fixtures with relative paths - `go test` sets CWD to the package directory:

```go
data, err := os.ReadFile("testdata/valid_user.json")
```

## Example Tests

Functions named `ExampleXxx()` serve as both tests and documentation:

```go
func ExampleReverse() {
    fmt.Println(Reverse("hello"))
    // Output: olleh
}
```

Appear in `go doc` output and run during `go test`.

## HTTP Testing

```go
func TestHandler(t *testing.T) {
    handler := NewHandler(mockService)

    req := httptest.NewRequest("GET", "/users/123", nil)
    w := httptest.NewRecorder()

    handler.ServeHTTP(w, req)

    assert.Equal(t, http.StatusOK, w.Code)
    assert.Contains(t, w.Body.String(), "alice")
}

func TestClient(t *testing.T) {
    srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        w.WriteHeader(http.StatusOK)
        json.NewEncoder(w).Encode(User{Name: "alice"})
    }))
    t.Cleanup(srv.Close)

    client := NewClient(srv.URL)
    user, err := client.GetUser("123")
    require.NoError(t, err)
    assert.Equal(t, "alice", user.Name)
}
```

## testcontainers-go

Spin up ephemeral infrastructure for integration tests:

```go
func TestPostgres(t *testing.T) {
    ctx := t.Context()

    container, err := postgres.Run(ctx, "postgres:17",
        postgres.WithDatabase("testdb"),
        postgres.WithUsername("test"),
        postgres.WithPassword("test"),
        testcontainers.WithWaitStrategy(
            wait.ForLog("database system is ready"),
        ),
    )
    require.NoError(t, err)
    t.Cleanup(func() { container.Terminate(ctx) })

    connStr, err := container.ConnectionString(ctx, "sslmode=disable")
    require.NoError(t, err)

    db, err := sql.Open("postgres", connStr)
    require.NoError(t, err)
    // Run tests against real database
}
```

## synctest (Go 1.25+)

Deterministic testing of concurrent code. The stable API in Go 1.25+ is `synctest.Test(t, fn)`; the experimental `synctest.Run(fn)` from Go 1.24 (under `GOEXPERIMENT=synctest`) was renamed and now takes a `*testing.T`:

```go
import "testing/synctest"

func TestConcurrent(t *testing.T) {
    synctest.Test(t, func(t *testing.T) {
        ch := make(chan int)
        go func() { ch <- 42 }()

        synctest.Wait() // Waits for all goroutines to block
        val := <-ch
        assert.Equal(t, 42, val)
    })
}
```

## Quick Reference: Test Flags

```bash
go test ./...                          # Run all tests
go test -v ./...                       # Verbose
go test -race ./...                    # Race detection
go test -short ./...                   # Skip slow tests
go test -run TestFoo ./...             # Run matching tests
go test -run TestFoo/subcase ./...     # Run specific subtest
go test -count=1 ./...                 # Disable test cache
go test -tags=integration ./...        # Build tag
go test -parallel 4 ./...              # Max parallel tests
go test -timeout 10m ./...             # Test timeout
go test -bench=. -benchmem ./...       # Benchmarks
go test -fuzz=FuzzParse ./...          # Fuzzing
go test -coverprofile=c.out ./...      # Coverage
go test -covermode=atomic ./...        # Atomic coverage
go test -coverpkg=./... ./...          # Cross-package coverage
```
