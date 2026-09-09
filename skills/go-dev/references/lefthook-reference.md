# Lefthook Reference

Latest: **v2.1.12** (2026-08-28). Single Go binary, no runtime dependency. `go install github.com/evilmartians/lefthook/v2@v2.1.12` needs Go 1.26+; Homebrew, npm, and the GitHub release binaries avoid that floor.

Config is discovered at the repo root or in `.config/`, and read fresh on every hook run - "Reinstall is not required when you modify `lefthook.yml`, the configuration file is read every time a git hook is run." Only adding or removing a *hook section* requires `lefthook install`.

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

Two more filtering surprises:

- **`**` matches one or more directories, not zero or more.** `glob: "src/**/*.go"` does *not* match `src/file.go`. Use separate patterns, or opt into standard semantics with `glob_matcher: doublestar`.
- **Globs ignore `root`.** "Globs are still calculated from the actual root of the git repo."

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
- **`fail_on_changes`** decides whether a job that modified tracked files fails: `never` (default), `always`, `ci` ("exit with a non-zero status only when the `CI` environment variable is set ... useful when combined with `stage_fixed` to ensure a frictionless devX locally, and a robust CI"), or `non-ci`.

## `stage_fixed`

Re-stages files after a fixer rewrote them. Since v2.1.12 a failed re-stage fails the hook - "If the `git add` call fails, the hook fails too. Otherwise the commit would silently go through with the unfixed content."

Unstaged work is safe across a hook run: lefthook hides unstaged changes for the hook's duration and restores them afterwards, so the gate judges exactly what is being committed, not your working tree. (Behaviour before 1.7 differed; ignore older accounts of this.)

## Guardrails

```yaml
assert_lefthook_installed: true   # exit 1 if the binary is missing, instead of skipping every rule
min_version: 2.1.12               # refuse to run under an older lefthook
```

`assert_lefthook_installed` is the fix for the dormancy failure mode - "fail (with exit status 1) if `lefthook` executable can't be found in $PATH, under node_modules/, as a Ruby gem, or other supported method."

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

Two install behaviours worth knowing:

- **A pre-existing foreign hook is preserved, not clobbered** - it is renamed to `.git/hooks/<hook>.old`, and `uninstall` restores it. This is what makes a pre-commit-to-lefthook migration safe.
- **`install -f` does not prune hooks you deleted from config.** It syncs the hooks it knows about; a shim for a removed hook keeps firing until you delete it from `.git/hooks` by hand.

## Environment Variables

| Variable | Effect |
|----------|--------|
| `LEFTHOOK=0` | Disable lefthook entirely for this command |
| `LEFTHOOK_EXCLUDE=job1,job2` | Skip named jobs |
| `LEFTHOOK_OUTPUT` | Control which output sections print |
| `LEFTHOOK_VERBOSE=1` | Verbose logging |
| `LEFTHOOK_BIN` | Path to the lefthook binary to use |
| `LEFTHOOK_CONFIG` | Path to the config file, overriding discovery |
| `CI` | Recognised by `fail_on_changes: ci` and skip/only conditions |
| `NO_COLOR` / `CLICOLOR_FORCE` | Disable / force colour |

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
