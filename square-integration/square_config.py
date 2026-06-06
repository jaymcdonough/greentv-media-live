#!/usr/bin/env python3
"""
Square integration config for GreenTV.
Keys from square_api_info.txt (sandbox for now).
Replace with production keys when ready.
Note: The provided token may need to be the full server access token from the Square Developer Dashboard (Apps > [your app] > Credentials).
For full auth, log into developer.squareup.com with the account, get the full token, and update here.
"""

SQUARE_CONFIG = {
    "application_id": "sq0idp-DlQo-Wshau1yyPw0VSJvag",
    "access_token": "EAAAl0ehJEdwyktBQ0flwznkMxcGuL3fJ60xt9fK4-aVAlQMEjXuXQfWhCzv0eeN",
    "environment": "production",
    "location_id": "LKQJNQYSED812",
    "webhook_url": "https://greentv.media/webhooks/square",
}

# GreenTV specific catalog items (populated via populate_catalog.py)
CATALOG_ITEMS = {
    "greentv_share": {
        "name": "GreenTV Share",
        "description": "Equity share in GreenTV at $1,000 per share. Fuels independent truth media, AI automation for creators, and Olivia Green segments.",
        "price": 100000,  # cents
        "currency": "USD",
    },
    "greentv_pro_membership": {
        "name": "GreenTV Pro Membership",
        "description": "Monthly: Automation + analytics for your custom channel. Hook up your sites and accounts to generate revenue.",
        "price": 4900,
        "currency": "USD",
        "recurring": True,
    },
    "greentv_studio_membership": {
        "name": "GreenTV Studio Membership",
        "description": "Monthly: Full video pipeline + Olivia Green interview access + advanced automation.",
        "price": 14900,
        "currency": "USD",
        "recurring": True,
    },
    "custom_investment": {
        "name": "Custom GreenTV Investment",
        "description": "On-the-fly custom product. Negotiated deal. Amounts over $1000 require approval.",
        "price": 0,  # dynamic
        "currency": "USD",
    },
}

def get_square_client():
    from square.client import Square
    from square.environment import SquareEnvironment
    env = SquareEnvironment.SANDBOX if SQUARE_CONFIG["environment"] == "sandbox" else SquareEnvironment.PRODUCTION
    return Square(
        token=SQUARE_CONFIG["access_token"],
        environment=env
    )

if __name__ == "__main__":
    print("Square config loaded. Application ID:", SQUARE_CONFIG["application_id"])
    print("Token length:", len(SQUARE_CONFIG["access_token"]))
    print("Note: If auth fails, visit developer.squareup.com/apps , select your sandbox app, and copy the full Production/Sandbox Access Token.")
# === PRODUCTION KEYS (add these when you have them) ===
# PRODUCTION_CONFIG = {
#     "application_id": "sq0idp-DlQo-Wshau1yyPw0VSJvag",
#     "access_token": "EAAAlxKdOQ0Igcr3kWREkKaPCTeq-INLdcYb3kZBHKBckPAYeg-VZOnTcl5Gg3_Q",
#     "environment": "production",
#     "location_id": "LC1JRAJBF5N0F",
# }

# To switch:
# SQUARE_CONFIG = PRODUCTION_CONFIG
# Then re-run populate_catalog.py
