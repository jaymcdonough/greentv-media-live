#!/usr/bin/env python3
"""
Populate Square Catalog with GreenTV items based on greentv.media prototype conceptions.
- $1000/share investment
- Membership levels (Pro $49/mo, Studio $149/mo)
- Custom investment (template for negotiated deals)

Run this after updating the token in square_config.py.
This will create the items in your Square catalog for use in payments, invoices, the blank Square website, and greentv.app.

Also creates customers in Square Customers API (for CRM replacement/sync).
"""

import sys
import time
import uuid
sys.path.append('.')
from square_config import get_square_client, SQUARE_CONFIG, CATALOG_ITEMS

def get_location_id():
    client = get_square_client()
    response = client.locations.list()
    if response.locations:
        loc = response.locations[0]
        print(f"Using location: {loc.id} ({loc.name})")
        return loc.id
    return None

def populate_catalog():
    client = get_square_client()
    location_id = get_location_id()
    if not location_id:
        print("ERROR: No location found. Cannot populate.")
        return
    
    print("Fetching existing catalog items...")
    try:
        pager = client.catalog.list(types="ITEM")
        existing_items = {}
        for obj in pager:
            if obj.type == "ITEM" and obj.item_data:
                existing_items[obj.item_data.name] = obj.id
        print(f"Found {len(existing_items)} existing items.")
    except Exception as e:
        print(f"Error listing catalog: {e}")
        existing_items = {}
    
    created = []
    for key, item_data in CATALOG_ITEMS.items():
        name = item_data["name"]
        if name in existing_items:
            print(f"Item '{name}' already exists (ID: {existing_items[name]}). Skipping.")
            continue
        
        print(f"Creating catalog item: {name} ...")
        
        idempotency_key = f"greentv-{key}-{int(time.time())}-{uuid.uuid4().hex[:8]}"
        object_id = f"#{key.upper().replace('_', '')}"
        var_id = f"#{key.upper().replace('_', '')}VAR"
        
        catalog_object = {
            "id": object_id,
            "type": "ITEM",
            "idempotency_key": idempotency_key,
            "item_data": {
                "name": name,
                "description": item_data["description"],
                "abbreviation": key[:4].upper(),
                "variations": [
                    {
                        "id": var_id,
                        "type": "ITEM_VARIATION",
                        "idempotency_key": f"greentv-{key}-var-{int(time.time())}",
                        "item_variation_data": {
                            "name": "Default",
                            "price_money": {
                                "amount": item_data["price"],
                                "currency": item_data.get("currency", "USD"),
                            },
                            "pricing_type": "FIXED_PRICING",
                        }
                    }
                ]
            }
        }
        
        try:
            response = client.catalog.batch_upsert(
                idempotency_key=idempotency_key,
                batches=[
                    {
                        "objects": [catalog_object]
                    }
                ]
            )
            
            if response.errors:
                print(f"  Error creating {name}: {response.errors}")
            else:
                print(f"  Created successfully for {name}")
                created.append(name)
        except Exception as e:
            print(f"  Exception creating {name}: {e}")
    
    print(f"\nCatalog population complete. Created: {created}")

def create_test_customer():
    client = get_square_client()
    print("\nCreating test customer for Square CRM (from prototype intake example)...")
    try:
        response = client.customers.create(
            given_name="Test",
            family_name="Investor",
            email_address="investor@green.tv.example",
            note="From greentv.media prototype - interested in $1000 share + automation revenue share. Routed via Square integration.",
            company_name="GreenTV Test Investor",
        )
        if hasattr(response, 'customer') and response.customer:
            cust = response.customer
            print(f"Test customer created: {cust.id} ({cust.email_address})")
            return cust.id
        elif hasattr(response, 'id'):
            print(f"Test customer created: {response.id}")
            return response.id
        else:
            print("Customer response:", response)
            return None
    except Exception as e:
        print(f"Customer creation error: {e}")
        return None

def test_create_payment_token_example():
    print("\n--- Payment example (use after Web Payments SDK tokenization in prototype/site) ---")
    print("In production code (process_payment.py):")
    print("  client.payments.create_payment(body={")
    print("      'source_id': 'cnon:card-nonce-ok-or-from-sdk',")
    print("      'idempotency_key': str(uuid.uuid4()),")
    print("      'amount_money': {'amount': 100000, 'currency': 'USD'},")
    print("      'note': 'GreenTV Share purchase via greentv.media',")
    print("      'location_id': 'LC1JRAJBF5N0F'")
    print("  })")
    print("This will appear in Square Dashboard > Payments and link to the CRM customer.")

if __name__ == "__main__":
    print("=== GreenTV Square Catalog + CRM Population ===")
    print("Using sandbox. Token updated by user.")
    populate_catalog()
    cust_id = create_test_customer()
    test_create_payment_token_example()
    print("\nDone. Check Square Dashboard:")
    print("  - Items (Catalog) for GreenTV Share, Pro Membership, Studio Membership")
    print("  - Customers for the test investor entry (CRM sync point)")
    print("  - Payments (once you complete a test payment from the prototype or greentv-square-site.html)")
    print("Update location_id in square_config.py if needed for greentv.media / greentv.app.")
