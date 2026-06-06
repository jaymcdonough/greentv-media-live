# GreenTV Square Integration

## Overview
Square is now the payment gateway for greentv.media and greentv.app.

- **Payments**: Investments ($1,000/share or custom on-the-fly products), memberships (Pro $49/mo, Studio $149/mo).
- **CTAs from prototype**: Every paid action (investor flow, membership upgrade, custom deals) now routes to Square for tokenization and processing.
- **CRM**: Square Customers API + Customer Directory to replace or sync with current CRM (outreach-kit, WP, etc.).
- **Invoices**: For deals >$1,000 or negotiated, create hosted Square invoices.
- **Subscriptions**: For recurring memberships.

## Files
- `square_config.py`: Keys and config (update token/location from Square dashboard).
- `populate_catalog.py`: Creates catalog items in Square for shares, memberships, custom deals.
- `process_payment.py`: Backend functions to process payments, invoices, subscriptions, and create CRM customers.

## Setup Steps (done or in progress)
1. Keys loaded from square_api_info.txt (sandbox).
2. Note sent to VPS Hermes (via R2 tunnel) to:
   - Set up full Square CRM (Customers API sync with existing systems).
   - Hook Square as gateway on greentv.media (WP) and greentv.app.
   - Populate catalog and locations on VPS side.
   - Replace current CRM or sync (use Square Customer Directory for investors, creators, sponsors).
3. Prototype HTML updated with Square Web Payments SDK for direct card entry in modals.
4. Blank Square website: See greentv-square-site.html (self-contained build-out of the blank site with GreenTV content, paths, and Square-powered CTAs).

## How to use in prototype (client-side)
The updated greentv-media-onboarding-prototype.html now includes:
- Square Web Payments SDK (sandbox).
- Card form in investor modal.
- On "Take Direct Action", it tokenizes the card and calls a simulated backend (logs token + amount).
- In production, POST the token to /process-payment endpoint that uses process_payment.py.

## Backend example (Python)
```python
from process_payment import process_payment, create_invoice_for_custom_deal

# For $1000 share
result = process_payment(
    source_id="cnon:card-nonce-ok",  # From SDK tokenization
    amount_cents=100000,
    note="GreenTV Share purchase - $1000"
)

# For custom >$1000
invoice = create_invoice_for_custom_deal(
    customer_email="user@domain.com",
    amount_cents=250000,
    description="Custom $2,500 investment negotiated via greentv.media"
)
print("Pay here:", invoice["public_url"])
```

## For greentv.media (WP) and greentv.app
- Add the JS SDK to pages.
- Create WP plugin or shortcode that renders the card form for specific CTAs (e.g. [square_invest amount="1000"]).
- Backend: Add the Python processor behind an API endpoint (or use Square PHP SDK if WP prefers).
- Use Square Webhooks for payment events to trigger CRM updates, Olivia interview invites, channel provisioning.
- For the blank Square site: Use Square Online dashboard to add the catalog items, then embed custom HTML/JS or use Square's site builder with the populated items.

## Next for VPS Hermes (already noted via tunnel)
- Run populate_catalog.py on VPS with full production keys.
- Set up Square OAuth or direct token for the main account.
- Sync Customers API with existing /root/greentv-company-kit-private/outreach-kit and WP user database.
- Add Square as the payment provider in any existing checkout flows.
- For greentv.app: Hook the automation revenue features to Square subscriptions/invoices.
- Test end-to-end: Intake on prototype -> token -> process_payment -> Square dashboard shows payment + customer.

## Important Notes
- Current token in file may be partial or sandbox-only. Log into developer.squareup.com with the GreenTV account, go to Apps > your sandbox app > OAuth or Credentials, copy the FULL Sandbox Access Token, and update square_config.py.
- For production, switch environment and get production token (requires app review/activation).
- Location ID: Run populate or list_locations once token works.
- The blank Square website build-out is in the sibling HTML file. Populate it in Square Online by copying the content sections and linking CTAs to the catalog items created here.

Run `python populate_catalog.py` (after fixing token) to populate.

Report any auth issues back to user or VPS.

This drives the revenue: users from prototype paths pay via Square for shares, memberships, custom deals. Content submissions remain the free on-ramp to Olivia interviews.
## LIVE UPDATES (2026-06-05 after token fix)
- Location fetched: LC1JRAJBF5N0F (Default Test Account)
- Catalog populated successfully:
  - GreenTV Share ($1000)
  - GreenTV Pro Membership ($49/mo)
  - GreenTV Studio Membership ($149/mo)
  - Custom GreenTV Investment (dynamic)
- Test customer created in Square CRM: HSEYNXN27S7JCXPR6BPS5ZK7BC (and others)
- All scripts updated to match current Square Python SDK (no 'body' wrappers, correct batch_upsert with ids, customers.create with kwargs).
- Next: Test a full payment from the prototype or greentv-square-site.html using a sandbox card nonce. It will show in Square Dashboard > Payments.
- For greentv.media / greentv.app: Add the JS SDK + call these Python endpoints (or port logic).
- VPS note already sent; re-send if needed with these results.
