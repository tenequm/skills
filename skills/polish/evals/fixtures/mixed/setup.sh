#!/usr/bin/env bash
# Creates a fixture repo with mixed issues across all three categories
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-mixed
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src/utils

# -- Initial commit: baseline with existing utilities --
cat > src/utils/format.ts << 'BASELINE'
export function formatCurrency(cents: number): string {
  return `$${(cents / 100).toFixed(2)}`;
}

export function formatDate(date: Date): string {
  return date.toISOString().split("T")[0];
}
BASELINE

cat > src/types.ts << 'BASELINE'
export interface Product {
  id: string;
  name: string;
  priceCents: number;
}

export interface CartItem {
  product: Product;
  quantity: number;
}
BASELINE

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: mixed issues --
cat > src/checkout.ts << 'CHANGED'
import type { CartItem, Product } from "./types";

// TODO: add caching here
export async function checkout(items: CartItem[]): Promise<string> {
  console.log("checkout called with", items.length, "items");

  // Calculate the total price by summing up all items
  let total = 0;
  for (const item of items) {
    total += item.product.priceCents * item.quantity;
  }

  // Hand-rolled currency format instead of using utils/format.ts
  const formatted = `$${(total / 100).toFixed(2)}`;

  // Sequential awaits on independent calls
  const tax = await calculateTax(total);
  const shipping = await calculateShipping(items);
  const discount = await calculateDiscount(items);

  const finalTotal = total + tax + shipping - discount;

  console.debug("final total:", finalTotal);
  return `$${(finalTotal / 100).toFixed(2)}`;
}

async function calculateTax(amount: number): Promise<number> {
  const rate = await fetch("/api/tax-rate").then((r) => r.json());
  return Math.round(amount * rate.value);
}

async function calculateShipping(items: CartItem[]): Promise<number> {
  const weight = items.reduce((sum, i) => sum + i.quantity, 0);
  const rate = await fetch("/api/shipping-rate").then((r) => r.json());
  return Math.round(weight * rate.perUnit);
}

async function calculateDiscount(items: CartItem[]): Promise<number> {
  const codes = await fetch("/api/discount-codes").then((r) => r.json());
  return 0;
}
CHANGED

git add -A

echo "$REPO_DIR"
