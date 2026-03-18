#!/usr/bin/env bash
# Creates a fixture repo with clean, well-written changes - should produce no findings
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-clean
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src

# -- Initial commit: baseline --
cat > src/types.ts << 'BASELINE'
export interface Config {
  apiUrl: string;
  timeout: number;
  retries: number;
}

export interface ApiResponse<T> {
  data: T;
  status: number;
}
BASELINE

cat > src/client.ts << 'BASELINE'
import type { Config, ApiResponse } from "./types";

const DEFAULT_TIMEOUT = 5000;

export function createClient(config: Config) {
  return {
    async get<T>(path: string): Promise<ApiResponse<T>> {
      const res = await fetch(`${config.apiUrl}${path}`, {
        signal: AbortSignal.timeout(config.timeout || DEFAULT_TIMEOUT),
      });
      const data = await res.json();
      return { data: data as T, status: res.status };
    },
  };
}
BASELINE

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: clean, well-written addition --
cat > src/health.ts << 'CHANGED'
import type { Config } from "./types";
import { createClient } from "./client";

const HEALTH_PATH = "/health";

export async function checkHealth(config: Config): Promise<boolean> {
  const client = createClient(config);
  const { status } = await client.get(HEALTH_PATH);
  return status === 200;
}
CHANGED

git add -A

echo "$REPO_DIR"
