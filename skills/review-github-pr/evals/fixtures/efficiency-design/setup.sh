#!/usr/bin/env bash
# Creates a fixture repo simulating a PR with efficiency and design issues.
# The repo has existing utilities (slugify, formatDate). The PR hand-rolls a slugify,
# uses sequential awaits on independent calls, and adds a TOCTOU file check.
set -euo pipefail

REPO_DIR=$(mktemp -d)/review-pr-eval-efficiency
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q

# ---- Base codebase on main: established patterns and utilities ----

mkdir -p src/utils src/routes src/services

# Existing utility: slugify
cat > src/utils/string.ts << 'BASE'
export function slugify(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

export function truncate(text: string, maxLen: number): string {
  if (text.length <= maxLen) return text;
  return text.slice(0, maxLen - 3) + "...";
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
BASE

# Existing utility: date formatting
cat > src/utils/dates.ts << 'BASE'
export function formatDate(date: Date): string {
  return date.toISOString().split("T")[0];
}

export function formatDateTime(date: Date): string {
  return date.toISOString().replace("T", " ").replace(/\.\d+Z$/, " UTC");
}

export function isExpired(date: Date): boolean {
  return date.getTime() < Date.now();
}
BASE

# Existing route pattern: uses Promise.all for independent fetches
cat > src/routes/dashboard.ts << 'BASE'
import { formatDate } from "../utils/dates";

interface DashboardData {
  stats: Stats;
  recentOrders: Order[];
  notifications: Notification[];
}

export async function getDashboard(userId: string): Promise<DashboardData> {
  const [stats, recentOrders, notifications] = await Promise.all([
    fetchStats(userId),
    fetchRecentOrders(userId),
    fetchNotifications(userId),
  ]);
  return { stats, recentOrders, notifications };
}

async function fetchStats(userId: string): Promise<Stats> {
  const res = await fetch(`/api/stats/${userId}`);
  return res.json();
}

async function fetchRecentOrders(userId: string): Promise<Order[]> {
  const res = await fetch(`/api/orders?user=${userId}&limit=10`);
  return res.json();
}

async function fetchNotifications(userId: string): Promise<Notification[]> {
  const res = await fetch(`/api/notifications/${userId}`);
  return res.json();
}
BASE

cat > src/services/product.ts << 'BASE'
import { slugify } from "../utils/string";

export interface Product {
  id: string;
  name: string;
  slug: string;
  price: number;
}

export function createProduct(name: string, price: number): Product {
  return {
    id: crypto.randomUUID(),
    name,
    slug: slugify(name),
    price,
  };
}
BASE

cat > package.json << 'BASE'
{ "name": "fixture-shop", "private": true }
BASE

git add -A && git commit -q -m "initial codebase"

# ---- PR branch: new blog feature with issues ----

git checkout -q -b feat/blog-posts

mkdir -p src/routes src/services

# New service with hand-rolled slugify (reuse opportunity) and TOCTOU pattern
cat > src/services/blog.ts << 'PR'
import * as fs from "fs";
import * as path from "path";

export interface BlogPost {
  id: string;
  title: string;
  slug: string;
  content: string;
  publishedAt: Date;
}

export function createBlogPost(title: string, content: string): BlogPost {
  // Hand-rolled slugify instead of using the existing utility
  const slug = title
    .toLowerCase()
    .trim()
    .replace(/[^\w\s-]/g, "")
    .replace(/[\s_]+/g, "-")
    .replace(/^-+|-+$/g, "");

  return {
    id: crypto.randomUUID(),
    title,
    slug,
    content,
    publishedAt: new Date(),
  };
}

export async function saveBlogImage(postId: string, imagePath: string): Promise<string> {
  const destDir = path.join("uploads", "blog", postId);

  // TOCTOU: checks existence before operating
  if (!fs.existsSync(destDir)) {
    fs.mkdirSync(destDir, { recursive: true });
  }

  const destPath = path.join(destDir, path.basename(imagePath));

  // TOCTOU: checks if file exists before reading
  if (fs.existsSync(imagePath)) {
    fs.copyFileSync(imagePath, destPath);
    return destPath;
  }

  throw new Error(`Image not found: ${imagePath}`);
}
PR

# New route with sequential awaits on independent calls
cat > src/routes/blog.ts << 'PR'
import { createBlogPost, type BlogPost } from "../services/blog";

interface BlogPageData {
  posts: BlogPost[];
  categories: string[];
  featuredPost: BlogPost | null;
  recentComments: Comment[];
}

export async function getBlogPage(): Promise<BlogPageData> {
  // Sequential awaits on independent data - should be parallel
  const posts = await fetchPosts();
  const categories = await fetchCategories();
  const featuredPost = await fetchFeaturedPost();
  const recentComments = await fetchRecentComments();

  return { posts, categories, featuredPost, recentComments };
}

export async function getPostBySlug(slug: string): Promise<BlogPost | null> {
  const res = await fetch(`/api/posts?slug=${slug}`);
  if (!res.ok) return null;
  return res.json();
}

async function fetchPosts(): Promise<BlogPost[]> {
  const res = await fetch("/api/posts");
  return res.json();
}

async function fetchCategories(): Promise<string[]> {
  const res = await fetch("/api/categories");
  return res.json();
}

async function fetchFeaturedPost(): Promise<BlogPost | null> {
  const res = await fetch("/api/posts/featured");
  if (!res.ok) return null;
  return res.json();
}

async function fetchRecentComments(): Promise<Comment[]> {
  const res = await fetch("/api/comments/recent");
  return res.json();
}
PR

git add -A && git commit -q -m "feat: add blog post service and routes"

# ---- Mock gh CLI ----

MOCK_BIN="$REPO_DIR/.mock-bin"
mkdir -p "$MOCK_BIN"

PR_DIFF=$(git diff main...feat/blog-posts)

cat > "$MOCK_BIN/gh" << MOCK
#!/usr/bin/env bash
case "\$*" in
  *"pr view"*"--json"*)
    echo '{"title":"feat: add blog post service and routes","body":"Adds blog post creation with slug generation and image uploads. Also adds the blog page route with data aggregation.","author":{"login":"bob"},"baseRefName":"main","headRefName":"feat/blog-posts"}'
    ;;
  *"pr diff"*)
    cat << 'DIFF'
${PR_DIFF}
DIFF
    ;;
  *"pr checkout"*)
    git checkout -q feat/blog-posts 2>/dev/null || true
    ;;
  *"pr review"*)
    echo "[mock] Would post review: \$*"
    ;;
  *)
    echo "mock gh: unhandled command: \$*" >&2
    exit 1
    ;;
esac
MOCK
chmod +x "$MOCK_BIN/gh"

# Switch back to main
git checkout -q main

cat > CLAUDE.md << 'DOC'
# Shop Frontend

TypeScript project. No lint/typecheck command configured for this fixture.
DOC

git add CLAUDE.md && git commit -q -m "add CLAUDE.md"

echo "REPO_DIR=$REPO_DIR"
echo "Run: export PATH=\"$MOCK_BIN:\$PATH\" && cd $REPO_DIR"
