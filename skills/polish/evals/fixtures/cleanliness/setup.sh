#!/usr/bin/env bash
# Creates a fixture repo with cleanliness issues: debug leftovers, AI slop, dead code
set -euo pipefail

REPO_DIR=$(mktemp -d)/polish-eval-cleanliness
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q
mkdir -p src

# -- Initial commit: clean baseline --
cat > src/handler.ts << 'BASELINE'
import { logger } from "./logger";

export interface Order {
  id: string;
  items: string[];
  total: number;
}

export async function processOrder(order: Order): Promise<void> {
  logger.info(`Processing order ${order.id}`);
  const validated = validateOrder(order);
  await saveOrder(validated);
  logger.info(`Order ${order.id} saved`);
}

function validateOrder(order: Order): Order {
  if (order.items.length === 0) throw new Error("Empty order");
  if (order.total <= 0) throw new Error("Invalid total");
  return order;
}

async function saveOrder(order: Order): Promise<void> {
  // writes to database
  await db.orders.insert(order);
}
BASELINE

cat > src/logger.ts << 'BASELINE'
export const logger = {
  info: (msg: string) => console.info(`[INFO] ${msg}`),
  error: (msg: string) => console.error(`[ERROR] ${msg}`),
};
BASELINE

cat > package.json << 'BASELINE'
{ "name": "fixture", "private": true }
BASELINE

git add -A && git commit -q -m "initial"

# -- Working changes: introduces cleanliness issues --
cat > src/handler.ts << 'CHANGED'
import { logger } from "./logger";

export interface Order {
  id: string;
  items: string[];
  total: number;
}

/**
 * Processes an order by validating it and saving it to the database.
 * @param order - The order to process
 * @returns A promise that resolves when the order is processed
 */
export async function processOrder(order: Order): Promise<void> {
  console.log("DEBUG: processing order", order);
  logger.info(`Processing order ${order.id}`);
  const validated = validateOrder(order);
  // increment counter
  let count = 0;
  count++;
  await saveOrder(validated);
  logger.info(`Order ${order.id} saved, count: ${count}`);
}

/**
 * Validates an order object.
 * Checks that the order has items and a positive total.
 * Throws an error if validation fails.
 * @param order - The order to validate
 * @returns The validated order
 */
function validateOrder(order: Order): Order {
  if (order.items.length === 0) throw new Error("Empty order");
  if (order.total <= 0) throw new Error("Invalid total");
  return order;
}

async function saveOrder(order: Order): Promise<void> {
  // writes to database
  await db.orders.insert(order);
}

// TODO: refactor this later
function processLegacy(order: Order): void {
  // not used anywhere
}

// function oldHandler(req: Request): Response {
//   const body = await req.json();
//   const order = parseOrder(body);
//   await processOrder(order);
//   return new Response("ok");
// }
CHANGED

git add -A

echo "$REPO_DIR"
