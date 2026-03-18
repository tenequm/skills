#!/usr/bin/env bash
# Creates a fixture repo with efficiency issues: sequential awaits, N+1, TOCTOU
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-efficiency
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src

# -- Initial commit: clean baseline --
cat > src/types.ts << 'BASELINE'
export interface User {
  id: string;
  name: string;
  email: string;
}

export interface UserProfile {
  user: User;
  posts: Post[];
  followers: number;
}

export interface Post {
  id: string;
  authorId: string;
  title: string;
  body: string;
}
BASELINE

cat > src/db.ts << 'BASELINE'
import type { User, Post } from "./types";

export async function getUser(id: string): Promise<User> {
  return db.query("SELECT * FROM users WHERE id = ?", [id]);
}

export async function getUserPosts(userId: string): Promise<Post[]> {
  return db.query("SELECT * FROM posts WHERE author_id = ?", [userId]);
}

export async function getFollowerCount(userId: string): Promise<number> {
  const result = await db.query("SELECT COUNT(*) as count FROM follows WHERE target_id = ?", [userId]);
  return result.count;
}

export async function getPostDetails(postId: string): Promise<Post> {
  return db.query("SELECT * FROM posts WHERE id = ?", [postId]);
}
BASELINE

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: introduces efficiency issues --
cat > src/handler.ts << 'CHANGED'
import { readFileSync, existsSync } from "node:fs";
import { getUser, getUserPosts, getFollowerCount, getPostDetails } from "./db";
import type { UserProfile, Post } from "./types";

// One-time setup - should NOT be flagged
async function initConfig(): Promise<Record<string, string>> {
  const config = await fetch("/api/config");
  const theme = await fetch("/api/theme");
  const features = await fetch("/api/features");
  return { ...await config.json(), ...await theme.json(), ...await features.json() };
}

// Sequential awaits on independent calls
export async function getUserProfile(userId: string): Promise<UserProfile> {
  const user = await getUser(userId);
  const posts = await getUserPosts(userId);
  const followers = await getFollowerCount(userId);

  return { user, posts, followers };
}

// N+1 query pattern
export async function getPostsWithDetails(postIds: string[]): Promise<Post[]> {
  const results: Post[] = [];
  for (const id of postIds) {
    const post = await getPostDetails(id);
    results.push(post);
  }
  return results;
}

// TOCTOU anti-pattern
export function loadConfig(path: string): Record<string, unknown> {
  if (!existsSync(path)) {
    throw new Error(`Config file not found: ${path}`);
  }
  const content = readFileSync(path, "utf-8");
  return JSON.parse(content);
}
CHANGED

git add -A

echo "$REPO_DIR"
