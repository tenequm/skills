#!/usr/bin/env bash
# Creates a fixture repo where a bugfix patches the only in-repo caller (a shell entrypoint) while the shared parser
# stays broken for the same input typed by any user of the CLI
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-wrong-layer
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src bin

# -- Initial commit: a CLI that hands everything after `--` to the browser, and an entrypoint that wraps it --
cat > src/args.ts << 'BASELINE'
/** Everything after the first `--` is passed to the browser verbatim. */
export function splitPassthrough(argv: string[]): string[] {
  const i = argv.indexOf("--");
  return i < 0 ? [] : argv.slice(i + 1);
}
BASELINE

cat > src/launch.ts << 'BASELINE'
import { splitPassthrough } from "./args";

// The browser stops reading flags at a literal `--`, so anything after one is treated as a URL.
export function browserArgv(argv: string[]): string[] {
  return [...splitPassthrough(argv), "--remote-debugging-port=9222", "--user-data-dir=/data/profile"];
}
BASELINE

cat > src/cli.ts << 'BASELINE'
import { spawn } from "node:child_process";
import { browserArgv } from "./launch";

// `browserd serve [--port=N] [-- <browser flags...>]`
spawn("chromium", browserArgv(process.argv.slice(2)), { stdio: "inherit" });
BASELINE

cat > bin/viewer-entrypoint.sh << 'BASELINE'
#!/usr/bin/env bash
# Container entrypoint for the viewer image: starts the CLI with a visible start page.
set -e
exec browserd "$@" -- about:blank --start-maximized
BASELINE
chmod +x bin/viewer-entrypoint.sh

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true, "bin": { "browserd": "src/cli.ts" } }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: fixes "viewer started with browser flags never opens the debug port" in the entrypoint only --
cat > bin/viewer-entrypoint.sh << 'CHANGED'
#!/usr/bin/env bash
# Container entrypoint for the viewer image: starts the CLI with a visible start page.
set -e
# A second `--` would make the browser read the debug-port flags as URLs, so add one only when missing.
separator=(--)
for arg in "$@"; do
  if [[ $arg == -- ]]; then
    separator=()
    break
  fi
done
exec browserd "$@" "${separator[@]}" about:blank --start-maximized
CHANGED

git add -A

echo "$REPO_DIR"
