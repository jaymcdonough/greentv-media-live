#!/usr/bin/env python3
"""
GreenTV Square Payment Processor.
Used for backend processing of payments from greentv.media and greentv.app prototype flows.
- Investments ($1000/share or custom)
- Membership signups (one-time or recurring via Subscriptions API)
- Custom deals

Call this from your WP plugin, greentv.app backend, or the prototype (for testing).

For the prototype HTML, the JS will tokenize and you can POST the token here for processing.

Also handles creating customers for the Square CRM sync.
"""

import sys
import uuid
sys.path.append('.')
from square_config import get_square_client, SQUARE_CONFIG

def process_payment(source_id, amount_cents, currency="USD", note="", customer_id=None, location_id=None):
    """
    Create a payment using a payment token (source_id) from Web Payments SDK.
    """
    client = get_square_client()
    
    if not location_id:
        location_id = SQUARE_CONFIG.get("location_id") or "LC1JRAJBF5N0F"
    
    idempotency_key = f"greentv-pay-{uuid.uuid4().hex[:24]}"
    
    response = client.payments.create(
        source_id=source_id,
        idempotency_key=idempotency_key,
        amount_money={"amount": amount_cents, "currency": currency},
        note=note or "GreenTV payment from prototype / site",
        location_id=location_id,
        customer_id=customer_id
    )
    
    # Check for errors in new SDK style
    if hasattr(response, 'errors') and response.errors:
        print("Payment error:", response.errors)
        return {"success": False, "errors": response.errors}
    else:
        # Assume success if no errors; payment is in response
        payment = getattr(response, 'payment', response)
        print("Payment successful!")
        print(f"  Payment ID: {getattr(payment, 'id', 'unknown')}")
        print(f"  Status: {getattr(payment, 'status', 'unknown')}")
        if hasattr(payment, 'amount_money'):
            print(f"  Amount: ${payment.amount_money.amount / 100}")
        return {"success": True, "payment": payment}

def create_invoice_for_custom_deal(customer_email, amount_cents, description, due_date=None):
    """
    For custom investments >$1000 or negotiated deals, create a Square Invoice.
    Escorts user to pay via Square hosted invoice.
    """
    client = get_square_client()
    
    # First ensure customer (use working create signature)
    try:
        cust_response = client.customers.create(
            email_address=customer_email,
            note="From GreenTV custom deal negotiation."
        )
        if hasattr(cust_response, 'customer'):
            customer = cust_response.customer
        else:
            customer = cust_response
    except Exception as e:
        return {"success": False, "errors": str(e)}
    
    invoice_body = {
        "invoice": {
            "location_id": SQUARE_CONFIG.get("location_id") or "LC1JRAJBF5N0F",
            "customer_id": getattr(customer, 'id', None),
            "payment_requests": [
                {
                    "request_type": "BALANCE",
                    "due_date": due_date or "2026-06-30",
                    "automatic_payment_source": "NONE",
                    "amount_money": {
                        "amount": amount_cents,
                        "currency": "USD"
                    }
                }
            ],
            "title": "GreenTV Custom Investment / Deal",
            "description": description,
            "delivery_method": "EMAIL",
        },
        "idempotency_key": f"greentv-invoice-{uuid.uuid4()}"
    }
    
    response = client.invoices.create_invoice(body=invoice_body)
    
    if hasattr(response, 'errors') and response.errors:
        return {"success": False, "errors": response.errors}
    else:
        invoice = getattr(response, 'invoice', response)
        public_url = getattr(invoice, 'public_url', 'Check Square Dashboard for invoice')
        print("Invoice created:", getattr(invoice, 'id', 'unknown'))
        print("Public URL:", public_url)
        return {"success": True, "invoice": invoice, "public_url": public_url}

def create_subscription_for_membership(customer_email, plan="pro"):
    """
    For recurring memberships using Square Subscriptions API.
    """
    client = get_square_client()
    
    try:
        cust_response = client.customers.create(
            email_address=customer_email
        )
        customer_id = getattr(getattr(cust_response, 'customer', cust_response), 'id', None)
    except Exception as e:
        customer_id = None
    
    print(f"Subscription request for {plan} membership for {customer_email}")
    print("In production: Create subscription plan in Square Dashboard and call Subscriptions API with plan ID.")
    print("Customer ID for CRM:", customer_id)
    
    return {"success": True, "customer_id": customer_id, "note": "Use Square Dashboard to finalize recurring billing or call Subscriptions API with plan ID."}

if __name__ == "__main__":
    print("GreenTV Square Payment Processor ready.")
    print("Example usage:")
    print("  process_payment('cnon:card-nonce-ok', 100000, note='Test $1000 share purchase')")
    print("  create_invoice_for_custom_deal('user@example.com', 500000, 'Custom $5000 investment deal')")
    print("Update location_id and test with real token from dashboard.")
