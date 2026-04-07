#!/usr/bin/env bash
# Creates a fixture repo simulating a clean PR with no issues.
# The PR follows all existing conventions, reuses utilities, and has no bugs.
# The skill should report LGTM.
set -euo pipefail

REPO_DIR=$(mktemp -d)/review-pr-eval-clean
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q

# ---- Base codebase on main ----

mkdir -p src/utils src/routes src/services

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
BASE

cat > src/utils/dates.ts << 'BASE'
export function formatDate(date: Date): string {
  return date.toISOString().split("T")[0];
}

export function isExpired(date: Date): boolean {
  return date.getTime() < Date.now();
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

cat > src/routes/products.ts << 'BASE'
import { createProduct, type Product } from "../services/product";

export async function listProducts(): Promise<Product[]> {
  const res = await fetch("/api/products");
  if (!res.ok) throw new Error(`Failed to fetch products: ${res.status}`);
  return res.json();
}

export async function getProduct(id: string): Promise<Product | null> {
  const res = await fetch(`/api/products/${id}`);
  if (!res.ok) return null;
  return res.json();
}
BASE

cat > package.json << 'BASE'
{ "name": "fixture-shop", "private": true }
BASE

git add -A && git commit -q -m "initial codebase"

# ---- PR branch: well-written new feature ----

git checkout -q -b feat/product-categories

mkdir -p src/services src/routes

# Clean service: reuses existing slugify, proper error handling, good patterns
cat > src/services/category.ts << 'PR'
import { slugify } from "../utils/string";

export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string;
}

export function createCategory(name: string, description: string): Category {
  return {
    id: crypto.randomUUID(),
    name,
    slug: slugify(name),
    description,
  };
}
PR

# Clean route: proper null handling, error checking, follows existing patterns
cat > src/routes/categories.ts << 'PR'
import { createCategory, type Category } from "../services/category";

export async function listCategories(): Promise<Category[]> {
  const res = await fetch("/api/categories");
  if (!res.ok) throw new Error(`Failed to fetch categories: ${res.status}`);
  return res.json();
}

export async function getCategory(id: string): Promise<Category | null> {
  const res = await fetch(`/api/categories/${id}`);
  if (!res.ok) return null;
  return res.json();
}

export async function createNewCategory(
  name: string,
  description: string,
): Promise<Category> {
  const category = createCategory(name, description);
  const res = await fetch("/api/categories", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(category),
  });
  if (!res.ok) throw new Error(`Failed to create category: ${res.status}`);
  return res.json();
}
PR

git add -A && git commit -q -m "feat: add product categories"

# ---- Mock gh CLI ----

MOCK_BIN="$REPO_DIR/.mock-bin"
mkdir -p "$MOCK_BIN"

PR_DIFF=$(git diff main...feat/product-categories)

cat > "$MOCK_BIN/gh" << MOCK
#!/usr/bin/env bash
case "\$*" in
  *"pr view"*"--json"*)
    echo '{"title":"feat: add product categories","body":"Adds category model and CRUD routes. Uses existing slugify utility for slug generation. Follows the same patterns as the product service.","author":{"login":"carol"},"baseRefName":"main","headRefName":"feat/product-categories"}'
    ;;
  *"pr diff"*)
    cat << 'DIFF'
${PR_DIFF}
DIFF
    ;;
  *"pr checkout"*)
    git checkout -q feat/product-categories 2>/dev/null || true
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

git checkout -q main

cat > CLAUDE.md << 'DOC'
# Shop Frontend

TypeScript project. No lint/typecheck command configured for this fixture.
DOC

git add CLAUDE.md && git commit -q -m "add CLAUDE.md"

echo "REPO_DIR=$REPO_DIR"
echo "Run: export PATH=\"$MOCK_BIN:\$PATH\" && cd $REPO_DIR"
