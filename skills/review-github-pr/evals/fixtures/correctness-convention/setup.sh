#!/usr/bin/env bash
# Creates a fixture repo simulating a PR with correctness bugs and convention violations.
# The repo has established patterns (named SQL constraints, Scan methods that return nil on default).
# The PR introduces a new type that deviates from both patterns and has a null safety bug.
set -euo pipefail

REPO_DIR=$(mktemp -d)/review-pr-eval-correctness
mkdir -p "$REPO_DIR"
cd "$REPO_DIR"
git init -q

# ---- Base codebase on main: established patterns ----

mkdir -p internal/models internal/api migrations

# Existing model with Scan/Value - established pattern: default case returns nil
cat > internal/models/status.go << 'BASE'
package models

import (
	"database/sql/driver"
	"fmt"
)

type OrderStatus string

const (
	OrderStatusPending   OrderStatus = "pending"
	OrderStatusConfirmed OrderStatus = "confirmed"
	OrderStatusShipped   OrderStatus = "shipped"
	OrderStatusCancelled OrderStatus = "cancelled"
)

func (s *OrderStatus) Scan(src interface{}) error {
	switch v := src.(type) {
	case string:
		*s = OrderStatus(v)
		return nil
	case []byte:
		*s = OrderStatus(string(v))
		return nil
	default:
		return nil
	}
}

func (s OrderStatus) Value() (driver.Value, error) {
	return string(s), nil
}
BASE

# Existing migration - established pattern: named CHECK constraints
cat > migrations/001_create_orders.sql << 'BASE'
CREATE TABLE orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id),
    status TEXT NOT NULL DEFAULT 'pending'
        CONSTRAINT chk_orders_status CHECK (status IN ('pending', 'confirmed', 'shipped', 'cancelled')),
    total_cents INTEGER NOT NULL
        CONSTRAINT chk_orders_total_positive CHECK (total_cents >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_orders_customer ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
BASE

cat > migrations/002_add_coupons.sql << 'BASE'
CREATE TABLE coupons (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT NOT NULL UNIQUE,
    discount_pct INTEGER NOT NULL
        CONSTRAINT chk_coupons_discount_range CHECK (discount_pct BETWEEN 1 AND 100),
    uses_remaining INTEGER NOT NULL DEFAULT 1
        CONSTRAINT chk_coupons_uses_positive CHECK (uses_remaining >= 0),
    expires_at TIMESTAMPTZ
);
BASE

# Existing API handler
cat > internal/api/orders.go << 'BASE'
package api

import (
	"encoding/json"
	"net/http"
)

type OrderHandler struct {
	db *DB
}

func (h *OrderHandler) GetOrder(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	order, err := h.db.GetOrder(r.Context(), id)
	if err != nil {
		http.Error(w, "not found", http.StatusNotFound)
		return
	}
	json.NewEncoder(w).Encode(order)
}
BASE

cat > go.mod << 'BASE'
module github.com/example/shop

go 1.22
BASE

git add -A && git commit -q -m "initial codebase"

# ---- PR branch: new Priority type with issues ----

git checkout -q -b feat/add-priority-type

# New model - deviates from convention: Scan returns error on default (existing returns nil),
# and also has a null safety bug (no nil check on src)
cat > internal/models/priority.go << 'PR'
package models

import (
	"database/sql/driver"
	"fmt"
)

type TicketPriority string

const (
	PriorityLow      TicketPriority = "low"
	PriorityMedium   TicketPriority = "medium"
	PriorityHigh     TicketPriority = "high"
	PriorityCritical TicketPriority = "critical"
)

func (p *TicketPriority) Scan(src interface{}) error {
	switch v := src.(type) {
	case string:
		*p = TicketPriority(v)
		return nil
	case []byte:
		*p = TicketPriority(string(v))
		return nil
	default:
		return fmt.Errorf("unsupported type for TicketPriority: %T", src)
	}
}

func (p TicketPriority) Value() (driver.Value, error) {
	return string(p), nil
}
PR

# New migration - deviates from convention: unnamed CHECK constraint
cat > migrations/003_add_tickets.sql << 'PR'
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title TEXT NOT NULL,
    description TEXT,
    priority TEXT NOT NULL DEFAULT 'medium'
        CHECK (priority IN ('low', 'medium', 'high', 'critical')),
    assignee_id UUID REFERENCES users(id),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX idx_tickets_priority ON tickets(priority);
PR

# New API handler with null safety bug: doesn't check if ticket exists before accessing fields
cat > internal/api/tickets.go << 'PR'
package api

import (
	"encoding/json"
	"net/http"
)

type TicketHandler struct {
	db *DB
}

func (h *TicketHandler) GetTicket(w http.ResponseWriter, r *http.Request) {
	id := r.PathValue("id")
	ticket, err := h.db.GetTicket(r.Context(), id)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	// Bug: ticket can be nil if not found, but we access .Title without checking
	response := map[string]interface{}{
		"id":       ticket.ID,
		"title":    ticket.Title,
		"priority": ticket.Priority,
	}
	json.NewEncoder(w).Encode(response)
}

func (h *TicketHandler) ListByPriority(w http.ResponseWriter, r *http.Request) {
	priority := r.URL.Query().Get("priority")
	tickets, err := h.db.ListTicketsByPriority(r.Context(), priority)
	if err != nil {
		http.Error(w, "internal error", http.StatusInternalServerError)
		return
	}
	json.NewEncoder(w).Encode(tickets)
}
PR

git add -A && git commit -q -m "feat: add ticket priority type and endpoints"

# ---- Mock gh CLI ----

MOCK_BIN="$REPO_DIR/.mock-bin"
mkdir -p "$MOCK_BIN"

PR_DIFF=$(git diff main...feat/add-priority-type)

cat > "$MOCK_BIN/gh" << MOCK
#!/usr/bin/env bash
case "\$*" in
  *"pr view"*"--json"*)
    echo '{"title":"feat: add ticket priority type and endpoints","body":"Adds a new TicketPriority custom type with Scan/Value and a migration for the tickets table. Also adds API endpoints for ticket CRUD.","author":{"login":"alice"},"baseRefName":"main","headRefName":"feat/add-priority-type"}'
    ;;
  *"pr diff"*)
    cat << 'DIFF'
${PR_DIFF}
DIFF
    ;;
  *"pr checkout"*)
    git checkout -q feat/add-priority-type 2>/dev/null || true
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

# Write a CLAUDE.md so the skill knows what to run
cat > CLAUDE.md << 'DOC'
# Shop Backend

Go service. No lint/typecheck command configured for this fixture.
DOC

git add CLAUDE.md && git commit -q -m "add CLAUDE.md"

echo "REPO_DIR=$REPO_DIR"
echo "Run: export PATH=\"$MOCK_BIN:\$PATH\" && cd $REPO_DIR"
