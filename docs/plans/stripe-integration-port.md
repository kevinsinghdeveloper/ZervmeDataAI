# Plan: Port Rich Stripe Integration from BE-ToStructured

## Context

The current Zerve app has a skeleton Stripe integration — 3 methods in StripeService, a single webhook event type, hardcoded `plan_tier: "professional"`, and no subscription lifecycle management. The old BE-ToStructured codebase has a much richer implementation with customer management, subscription CRUD, product/price admin, and 6 webhook event types. We're porting those patterns into the current DynamoDB-based, org-level billing architecture.

**Key architectural difference**: The old codebase does per-user billing (user.stripe_customer_id). Zerve does per-org billing (organization.stripe_customer_id). All ported code must be adapted to query/update organizations, not users.

---

## Part 1: Expand StripeService (backend)

### `backend/services/stripe/StripeService.py`

Currently has 3 methods. Expand to match old codebase's 13 methods, adapted for org-level billing:

**Add customer management:**
- `create_customer(email, name, metadata)` → calls `stripe.Customer.create()`
- `get_customer(customer_id)` → calls `stripe.Customer.retrieve()`
- `update_customer(customer_id, **kwargs)` → calls `stripe.Customer.modify()`

**Add subscription management:**
- `create_subscription(customer_id, price_id, metadata)` → creates subscription with `payment_behavior: "default_incomplete"`
- `get_subscription(subscription_id)` → retrieve subscription
- `cancel_subscription(subscription_id, at_period_end=True)` → cancel at period end or immediately
- `update_subscription(subscription_id, price_id)` → swap price on existing subscription

**Add product/price admin:**
- `create_product(name, description)` → creates Stripe product
- `create_price(product_id, amount_cents, currency, interval)` → creates recurring price
- `list_prices(product_id=None)` → lists active prices

**Add webhook construction:**
- `construct_event(payload, sig_header)` → `stripe.Webhook.construct_event()` using `self.webhook_secret`

**Refactor `handle_webhook()`** → Expand from 1 event to 6 events, adapted for org-level:
- `checkout.session.completed` → Look up org from metadata `org_id`, set `stripe_customer_id`, `stripe_subscription_id`, `subscription_status: "active"`, and `plan_tier` from plan lookup (not hardcoded)
- `customer.subscription.created` → Find org by `StripeCustomerIndex`, update `stripe_subscription_id` + `subscription_status`
- `customer.subscription.updated` → Find org by stripe_subscription_id scan, update `subscription_status`. If canceled/unpaid → downgrade to "free"
- `customer.subscription.deleted` → Set `subscription_status: "canceled"`, clear `stripe_subscription_id`, downgrade to "free"
- `invoice.payment_succeeded` → Find org by `StripeCustomerIndex`, set `subscription_status: "active"`
- `invoice.payment_failed` → Set `subscription_status: "past_due"`

**Dev fallback**: If `STRIPE_WEBHOOK_SECRET` not set, skip signature verification and parse payload as JSON (like old codebase).

All lazy-import `stripe` only when called (current pattern). Keep `set_db()` for DynamoDB access.

---

## Part 2: Add `subscription_status` to Organization schema

### `backend/database/schemas/organization.py`

Add field:
```python
subscription_status: Optional[str] = None  # active | canceled | past_due | unpaid
```

Update `to_item()`, `to_api_dict()` (as `subscriptionStatus`), and `from_item()`.

### `frontend/src/types/index.ts`

Add to `Organization` interface:
```typescript
subscriptionStatus?: string;
```

---

## Part 3: Add `stripe_product_id` to SubscriptionPlan schema

### `backend/database/schemas/subscription_plan.py`

Add field:
```python
stripe_product_id: Optional[str] = None
```

Update `to_item()`, `to_api_dict()` (as `stripeProductId`), `from_item()`.

---

## Part 4: Expand BillingResourceManager

### `backend/managers/billing/BillingResourceManager.py`

**Add new POST actions:**

- `cancel` — Cancel org's subscription via `stripe_service.cancel_subscription()`. If immediate cancel, downgrade org to "free" plan_tier and set `subscription_status: "canceled"`.
- `sync_plans` — Admin action: iterate active plans, create Stripe products/prices for plans without `stripe_price_id`, update DB. Skip free plans and already-synced plans. (Ported from old `PlanResourceManager.sync_to_stripe()`)

**Improve `_checkout()`:**
- If org has no `stripe_customer_id`, create a Stripe customer first using org owner's email/name, store it on the org. (Ported from old `SubscriptionResourceManager._create_checkout_session()`)
- Pass `plan_id` in metadata alongside `org_id` so webhook can look up the correct plan_tier instead of hardcoding

**Improve `_current()`:**
- Also return `subscriptionStatus` from org

---

## Part 5: Expand BillingController

### `backend/controllers/billing/BillingController.py`

Add routes:
- `POST /api/billing/cancel` → `cancel_subscription` (token_required) — action: "cancel"
- `POST /api/billing/sync-plans` → `sync_plans` (token_required + super_admin check) — action: "sync_plans"

---

## Part 6: Frontend — Cancel subscription + status display

### `frontend/src/utils/api.service.ts`

Add:
```typescript
async cancelSubscription(atPeriodEnd: boolean = true) {
  const response = await this.api.post('/api/billing/cancel', { atPeriodEnd });
  return response.data;
}
```

### `frontend/src/components/pages/OrgSettingsPage.tsx`

Billing tab additions:
- Show `subscriptionStatus` badge (active/past_due/canceled) next to current plan
- Add "Cancel Subscription" button (with confirmation dialog) for non-free plans
- On cancel success, refresh org data

---

## Part 7: Update seed script + add plan_tier lookup in webhook

### `backend/scripts/seed_subscription_plans.py`

Add `stripe_product_id` field to plan definitions (empty string, populated by sync-plans).

---

## Part 8: Update tests

### `backend/tests/test_stripe_service.py`

Add tests for new methods: `create_customer`, `cancel_subscription`, `construct_event`, expanded `handle_webhook` with 6 event types.

### `backend/tests/test_billing_manager.py`

Add tests for: cancel action, sync_plans action, checkout with customer creation, webhook plan_tier from metadata.

---

## Files Summary

| File | Action | Changes |
|------|--------|---------|
| `backend/services/stripe/StripeService.py` | **Rewrite** | 3 → 13 methods, 6 webhook events, org-level lookups |
| `backend/managers/billing/BillingResourceManager.py` | Modify | Add cancel, sync_plans actions; improve checkout with customer creation |
| `backend/controllers/billing/BillingController.py` | Modify | Add /cancel, /sync-plans routes |
| `backend/database/schemas/organization.py` | Modify | Add `subscription_status` field |
| `backend/database/schemas/subscription_plan.py` | Modify | Add `stripe_product_id` field |
| `backend/scripts/seed_subscription_plans.py` | Modify | Add `stripe_product_id` to plan defs |
| `backend/tests/test_stripe_service.py` | Modify | Tests for new methods + webhook events |
| `backend/tests/test_billing_manager.py` | Modify | Tests for cancel, sync_plans, improved checkout |
| `frontend/src/types/index.ts` | Modify | Add `subscriptionStatus` to Organization |
| `frontend/src/utils/api.service.ts` | Modify | Add `cancelSubscription()` |
| `frontend/src/components/pages/OrgSettingsPage.tsx` | Modify | Cancel button, status badge |

---

## Verification

1. `cd backend && pytest tests/ -m "not postgres" -v` — all tests pass including new billing/stripe tests
2. `cd frontend && CI=true npm run build` — build passes
3. Manual: Without Stripe keys, billing endpoints return 503 "Billing not configured" (graceful degradation)
4. With test keys: checkout creates session, webhook updates org, cancel works, sync-plans creates Stripe products