# Lefthook Reference

Latest: **v2.1.15** (2026-09-29). Single Go binary, no runtime dependency. `go install github.com/evilmartians/lefthook/v2@v2.1.15` needs Go 1.26+; Homebrew, npm, and the GitHub release binaries avoid that floor.

Config is discovered at the repo root or in `.config/`, and read fresh on every hook run - "Reinstall is not required when you modify `lefthook.yml`, the configuration file is read every time a git hook is run." Only adding or removing a *hook section* requires `lefthook install`.

## v2.1.15 Notes

- **The shim fix needs a reinstall.** "fix: quote paths in the generated hook shim" ([#1509](https://github.com/evilmartians/lefthook/pull/1509)) shell-escapes the lefthook binary path baked into `.git/hooks/<hook>` (`internal/templates/hook.tmpl:36-38`). Upgrading the binary alone changes nothing; the fix lands only once `lefthook install` rewrites the shims.
- **Forced colours reach your jobs.** "feat: propagate forced colors to hook commands via CLICOLOR_FORCE" ([#1547](https://github.com/evilmartians/lefthook/pull/1547)): with colours explicitly on, lefthook sets `CLICOLOR_FORCE=1` for the commands it runs - "An existing `CLICOLOR_FORCE` is never overwritten."
- **Vulnerable dependencies in your module graph.** v2.1.15's `go.mod` pins `golang.org/x/mod v0.37.0` and `golang.org/x/text v0.38.0`, which carry [GO-2026-6179](https://pkg.go.dev/vuln/GO-2026-6179) and [GO-2026-6180](https://pkg.go.dev/vuln/GO-2026-6180) (x/mod, fixed in 0.40.0) and [GO-2026-5970](https://pkg.go.dev/vuln/GO-2026-5970) (x/text, fixed in 0.39.0). The bump is only on master ([#1560](https://github.com/evilmartians/lefthook/pull/1560)), so a lefthook tracked with `go get -tool` pulls those versions into your module graph, and module-level scanners (`govulncheck -scan module`, Dependabot, osv-scanner) may flag it until 2.1.16. The default `govulncheck ./...` symbol scan reports only code your packages reach.

## Job Filtering (the part that silently skips work)

**`glob` gates the job even when `run` has no file template.** This is the trap. The obvious reading is that `glob` only filters the list passed to `{staged_files}`, but the docs are explicit:

> If you've specified `glob` but don't have a files template in `run` option, lefthook will check `{staged_files}` for `pre-commit` hook and `{push_files}` for `pre-push` hook and apply filtering. If no files left, the command will be skipped.

So a whole-project job carrying a glob quietly does nothing on commits that touch no matching file:

```yaml
pre-commit:
  commands:
    # WRONG when you want this to always run: skipped on a docs-only commit
    typecheck:
      glob: "*.go"
      run: go build ./...
```

**Rule of thumb: a job that checks the project carries no `glob`; a job that consumes `{staged_files}` keeps one.** For `go mod tidy` the glob is right - a commit touching no `.go`, `.mod`, or `.sum` file genuinely has nothing to tidy - but that should be a decision, not an accident.

Three more filtering surprises:

- **`exclude` gates the job exactly like `glob`.** "If you've specified `exclude` but don't have a files template in `run` option, lefthook will check `{staged_files}` for `pre-commit` hook and `{push_files}` for `pre-push` hook and apply filtering. If no files left, the command will be skipped."
- **`**` matches one or more directories, not zero or more.** `glob: "src/**/*.go"` does *not* match `src/file.go`. Use separate patterns, or opt into standard semantics with `glob_matcher: doublestar`.
- **Globs ignore `root`.** "Globs are still calculated from the actual root of the git repo."

## Skipping During Rebase and Merge

`skip` takes `true`, or a list of conditions (`docs/configuration/skip.md`): `merge` ("when in merge git state"), `rebase` ("when in rebase git state"), `merge-commit` ("when current HEAD commit is the merge commit"), `ref: <branch>` (globs allowed, e.g. `ref: dev/*`), and `run: <cmd>` (skip when the command exits 0). It works on a single job or on the whole hook.

Skip `go mod tidy` and lint jobs in rebase and merge state, so they do not fire on the commits you make while resolving conflicts:

```yaml
pre-commit:
  commands:
    mod-tidy:
      glob: "*.{go,mod,sum}"
      skip:
        - merge
        - rebase
      run: go mod tidy
    lint:
      skip:
        - merge
        - rebase
      run: golangci-lint run ./...
```

## File Templates

| Template | Contents |
|----------|----------|
| `{staged_files}` | Staged files (`pre-commit`) |
| `{push_files}` | Files in the push range (`pre-push`) |
| `{all_files}` | All tracked files |
| `{files}` | Output of the job's custom `files` command |

## Monorepos: `root`

`root` changes the working directory for the job - "You can change the CWD for the command you execute using `root` option." Without it, `go mod tidy` and `go tool` run at the repo root and fail against a module that lives deeper:

```yaml
pre-commit:
  commands:
    mod-tidy:
      root: "services/api/"
      glob: "services/api/**/*.{go,mod,sum}"
      run: go mod tidy
```

## Ordering and Failure Behaviour

- **Sequential is the default.** "Lefthook runs commands and scripts **sequentially** by default." `parallel: true` opts into concurrency; `piped: true` is fail-fast - "Stop running commands and scripts if one of them fail." The two are mutually exclusive and lefthook errors if both are set.
- **`priority`** orders jobs when `parallel: false` or `piped: true`. Values run low-to-high from 1; "Value `0` is considered an `+Infinity`", so unprioritised jobs run last.
- **`commands:` is a map, and lefthook sorts it before running it.** Written order is not run order. The sort is `priority` first (0 last), then a leading numeric prefix in the name, then plain alphabetical comparison of the names (`internal/config/command.go:60-92`, same logic in `internal/config/script.go:54-85`). So a `piped: true` block of unprioritised commands runs alphabetically: `fmt` before `secrets`, `lint` before `test`. `jobs:` is a list and preserves declaration order - and its `Job` struct carries no `Priority` field at all, so `priority` is a `commands:`/`scripts:` option only.
- **`setup`** (2.1.2+) runs first - "A list of instructions to run before any job." When configs merge, `setup` entries from `lefthook-local.yml` or `extends` "get **prepended**".
- **`fail_on_changes`** decides whether a job that modified tracked files fails: `never` (default), `always`, `ci` ("exit with a non-zero status only when the `CI` environment variable is set ... useful when combined with `stage_fixed` to ensure a frictionless devX locally, and a robust CI"), or `non-ci`.

## `stage_fixed`

Re-stages files after a fixer rewrote them. Since v2.1.12 a failed re-stage fails the hook - "If the `git add` call fails, the hook fails too. Otherwise the commit would silently go through with the unfixed content."

**It re-stages the substituted file list, not the files the command actually touched.** Lefthook stages the same list it handed the job - the filtered `{staged_files}` expansion, or the filtered staged set when the job used no file template (`internal/run/controller/job.go:155-181`). A file the command *created*, or fixed while absent from that list, is left unstaged and the commit goes through without the fix.

**Unstaged work is hidden only for *partially staged* files.** The guard asks git for files dirty in *both* the index and the worktree, and if that list is empty it runs the hook with no stash at all (`internal/git/repo.go:228-246`, `internal/run/controller/guard.go:68-88`). A file carrying only unstaged changes - never `git add`ed - is not hidden, so the hook judges the on-disk file, not the indexed one. Verified live: an unstaged `Justfile` edit was the version the hook executed. Treat any claim that lefthook hides *all* unstaged changes for the hook's duration as wrong for 2.1.15.

**Worktree hazard: the backup is shared across linked worktrees.** The partial-stage backup patch lands at `.git/info/lefthook-unstaged.patch` and the safety stash is stored under the message `lefthook auto backup` (`internal/git/repo.go:24-25`, `:170`). Both resolve through the *common* git dir - `git rev-parse --git-path info` and `refs/stash` are shared, not per worktree - so every linked worktree of a repo contends for one patch file and one stash entry, and two worktrees committing concurrently can destroy each other's unstaged changes. Open upstream, both unfixed in 2.1.15: [the shared backup patch and stash across linked worktrees](https://github.com/evilmartians/lefthook/issues/1529), and [a failed patch re-apply falling back to a bare `git checkout .`](https://github.com/evilmartians/lefthook/issues/1480), which discards unstaged changes in unrelated files too (`internal/git/repo.go:46`, `:302`).

## Guardrails

```yaml
assert_lefthook_installed: true   # bake an exit-1-if-missing check into the installed hook script
min_version: 2.1.15               # refuse to run under an older lefthook
```

`assert_lefthook_installed` is the fix for the dormancy failure mode - "fail (with exit status 1) if `lefthook` executable can't be found in $PATH, under node_modules/, as a Ruby gem, or other supported method."

**But it is not a runtime guard.** The flag is only a template argument, baked into the generated `.git/hooks/<hook>` script at `lefthook install` time (`internal/command/install.go:332`, `internal/templates/hook.tmpl:100-105`); nothing in `lefthook run` ever reads it. Flipping it in config changes nothing until you reinstall, and it does nothing at all for a CI job that invokes `lefthook run` directly.

If you add a secret scanner, give it `priority: 1` so it runs before any formatter - otherwise a fixer can rewrite the file holding a credential before the scan ever reads it:

```yaml
pre-commit:
  piped: true
  commands:
    secrets:
      priority: 1
      run: your-secret-scanner {staged_files}   # check your scanner's own staged-scan flags
    fmt:
      glob: "*.go"
      run: golangci-lint fmt {staged_files}
      stage_fixed: true
```

## Sharing Config

- **`extends:`** merges other local config files into this one.
- **`remotes:`** pulls shared config from a git repo (`git_url`, `ref`, `configs`), with `refetch` and `refetch_frequency` controlling staleness. Useful for one lint policy across many services.
- **`lefthook-local.yml`** is the gitignored per-developer override - "useful when you want to use lefthook locally without imposing it on your teammates."
- **`templates:`** (1.10.8+) defines `{name}` placeholders for `run`, which `lefthook-local.yml` can override - "what can be overridden via `lefthook-local.yml` without a need to overwrite every jobs in your configuration." Ship an empty wrapper, and let a developer who runs tools in a container fill it in locally:

```yaml
# lefthook.yml
templates:
  wrap: # empty
pre-commit:
  commands:
    lint:
      run: "{wrap} golangci-lint run ./..."
```

```yaml
# lefthook-local.yml
templates:
  wrap: docker compose run --rm dev
```

Named jobs merge across `extends` and local config; unnamed jobs append in definition order.

## CLI

| Command | Purpose |
|---------|---------|
| `lefthook install` | Write the git hook shims; `install <hook>...` for specific hooks |
| `lefthook uninstall` | Remove shims and restore any `.old` hooks |
| `lefthook run <hook>` | Run a hook manually (this is what CI should call) |
| `lefthook validate` | Check the config is well-formed |
| `lefthook dump` | Print the merged effective config |
| `lefthook add <hook>` | Scaffold a hook and its script directory |
| `lefthook check-install` | Report whether hooks are installed |
| `lefthook self-update` | Update the binary in place |
| `lefthook version` | Print the version (`--full` includes the commit) |

Three install behaviours worth knowing:

- **A pre-existing foreign hook is preserved, not clobbered** - it is renamed to `.git/hooks/<hook>.old`, and `uninstall` restores it. This is what makes a pre-commit-to-lefthook migration safe.
- **A set `core.hooksPath` leaves hooks dormant.** If it is set locally (to anything but `.git/hooks`) or globally - a leftover husky or pre-commit setup, say - `lefthook install` logs an error and writes no hooks (`internal/command/install.go:97`, `:514-551`); the npm postinstall stops the same way (`docs/usage/commands/install.md:18`). `--force` ("overwrite .old files and proceed even if core.hooksPath is set") installs into the `core.hooksPath` directory; `--reset-hooks-path` ("automatically unset core.hooksPath configuration") unsets it - the global value too, if one is set (`:592-605`).
- **`install -f` does not prune hooks you deleted from config.** It syncs the hooks it knows about; a shim for a removed hook keeps firing until you delete it from `.git/hooks` by hand.

## Lefthook and Hook Tools as Go Tools

Track lefthook in `go.mod` (`docs/installation/go.md`) and point the shim at it with the `lefthook:` key - "Provide a full path to lefthook executable or a command to run lefthook. Bourne shell (`sh`) syntax is supported."

```bash
go get -tool github.com/evilmartians/lefthook/v2@v2.1.15
go tool lefthook install
```

```yaml
# lefthook.yml
lefthook: go tool lefthook
```

The value is baked into the shim at install time and tried before any PATH lookup, with only `LEFTHOOK_BIN` ahead of it (`internal/templates/hook.tmpl:18-24`), so every clone runs the version pinned in `go.mod`. It is not merged from `remotes` or `extends`. `go tool` resolves against the current module and git runs hooks from the worktree root, so this form assumes `go.mod` sits at the root.

The same applies to the jobs themselves: hook commands resolve tools from the caller's PATH, so a developer without the binary gets a commit that fails with a bare `exit 127`. Track hook tools with `go get -tool` and run them through `go tool` to make them reproducible:

```yaml
pre-commit:
  commands:
    lint:
      run: go tool golangci-lint run ./...
```

## Environment Variables

| Variable | Effect |
|----------|--------|
| `LEFTHOOK=0` / `LEFTHOOK=false` | Disable lefthook entirely for this command |
| `LEFTHOOK_EXCLUDE=job1,job2` | Skip named jobs |
| `LEFTHOOK_OUTPUT` | Control which output sections print |
| `LEFTHOOK_VERBOSE=1` | Verbose logging |
| `LEFTHOOK_BIN` | Path to the lefthook binary to use |
| `LEFTHOOK_CONFIG` | Path to the config file, overriding discovery |
| `CI` | Recognised by `fail_on_changes: ci` and skip/only conditions |
| `NO_COLOR` / `CLICOLOR_FORCE` | Disable / force colour |

**`LEFTHOOK=0` fails silently open.** `lefthook run` checks the variable before anything else and returns success having done nothing (`internal/command/run.go:49`, which also accepts `false`), and the generated `.git/hooks/*` script exits 0 on the literal `0` before it even looks for the binary (`internal/templates/hook.tmpl:7-9`). A CI job that inherits `LEFTHOOK=0` from its environment goes green without running a single check, and nothing in the output says so.

## Agent Hooks (`ai:`, beta)

Declares LLM agent hooks in the same config - "During `lefthook install`, lefthook generates the provider-specific settings file so that the agent calls `lefthook run <hook>` when the event fires." Providers and their generated files: `claude` (`.claude/settings.json`), `codex` (`.codex/hooks.json`), `cursor` (`.cursor/hooks.json`), `copilot` (`.github/hooks/lefthook.json`).

```yaml
ai:
  claude:
    Stop: validate
```

Keys under a provider must be that provider's own event names. Claude, Codex, and Cursor keep user-authored entries in their settings files across install and uninstall; Copilot's file is rewritten wholesale.

## CI

Run hooks in CI through `lefthook run`, and validate the config so a malformed file cannot silently disable every rule:

```yaml
- run: lefthook validate
- run: lefthook run pre-commit --all-files
```
