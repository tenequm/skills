#!/usr/bin/env bash
# Creates a fixture repo with design issues: missed reuse, over-engineering, stringly-typed code
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-design
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src/utils src/routes

# -- Initial commit: baseline with existing utilities --
cat > src/utils/string.ts << 'BASELINE'
/** Convert a string to a URL-safe slug */
export function slugify(input: string): string {
  return input
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

/** Truncate a string to maxLen, adding ellipsis if needed */
export function truncate(input: string, maxLen: number): string {
  if (input.length <= maxLen) return input;
  return input.slice(0, maxLen - 3) + "...";
}
BASELINE

cat > src/utils/http.ts << 'BASELINE'
export async function fetchJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  return res.json() as Promise<T>;
}
BASELINE

cat > src/types.ts << 'BASELINE'
export enum Status {
  Pending = "pending",
  Active = "active",
  Completed = "completed",
  Failed = "failed",
}

export interface Task {
  id: string;
  title: string;
  status: Status;
}
BASELINE

cat > src/routes/tasks.ts << 'BASELINE'
import { Status } from "../types";

export function getActiveTasks(tasks: Task[]): Task[] {
  return tasks.filter((t) => t.status === Status.Active);
}
BASELINE

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: introduces design issues --
cat > src/routes/articles.ts << 'CHANGED'
import { fetchJson } from "../utils/http";

interface Article {
  id: string;
  title: string;
  body: string;
  status: string;
}

// Hand-rolled slugify instead of using utils/string.ts
function makeSlug(title: string): string {
  return title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

// Single-use wrapper that adds nothing over fetchJson
async function fetchWithRetry(url: string): Promise<unknown> {
  return fetchJson(url);
}

export async function createArticle(title: string, body: string): Promise<Article> {
  const slug = makeSlug(title);

  const article: Article = {
    id: slug,
    title,
    body,
    status: "pending",  // raw string instead of Status.Pending
  };

  await fetchWithRetry("/api/articles");
  return article;
}

export async function publishArticle(article: Article): Promise<Article> {
  if (article.status === "pending") {  // raw string instead of Status enum
    return { ...article, status: "active" };  // raw string again
  }
  throw new Error("Cannot publish article with status: " + article.status);
}
CHANGED

git add -A

echo "$REPO_DIR"
