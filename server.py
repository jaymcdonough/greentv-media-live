#!/usr/bin/env python3
"""
GreenTV FastAPI server for greentv.media
Serves the prototype as main page + Square payment processing endpoint.
"""

import sys
import os
import uvicorn
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import subprocess
import json

# Add square-integration to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'square-integration'))
from process_payment import process_payment, create_invoice_for_custom_deal

app = FastAPI(title="GreenTV", version="1.0.0")

PROTOTYPE_PATH = os.path.join(os.path.dirname(__file__), 'greentv-media-onboarding-prototype.html')


class PaymentRequest(BaseModel):
    source_id: str
    amount_cents: int
    currency: str = "USD"
    note: str = ""
    customer_id: str | None = None
    location_id: str | None = None


@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def main_page():
    """Serve the GreenTV prototype as the main page."""
    if os.path.exists(PROTOTYPE_PATH):
        with open(PROTOTYPE_PATH, 'r') as f:
            return f.read()
    return HTMLResponse("<h1>GreenTV prototype not found</h1>", status_code=404)


@app.post("/api/process-payment")
async def api_process_payment(request: PaymentRequest):
    """Process a payment using Square Web Payments SDK nonce."""
    try:
        result = process_payment(
            source_id=request.source_id,
            amount_cents=request.amount_cents,
            currency=request.currency,
            note=request.note,
            customer_id=request.customer_id,
            location_id=request.location_id
        )
        if result.get("success"):
            payment = result.get("payment")
            return {
                "success": True,
                "payment_id": getattr(payment, 'id', None),
                "status": getattr(payment, 'status', None),
                "amount": getattr(payment, 'amount_money', {}).get('amount', request.amount_cents)
            }
        else:
            raise HTTPException(status_code=400, detail=result.get("errors", "Payment failed"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/create-invoice")
async def api_create_invoice(
    customer_email: str = Form(...),
    amount_cents: int = Form(...),
    description: str = Form(...),
    due_date: str | None = Form(None)
):
    """Create a Square Invoice for custom deals >$1000."""
    try:
        result = create_invoice_for_custom_deal(
            customer_email=customer_email,
            amount_cents=amount_cents,
            description=description,
            due_date=due_date
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "greentv-media"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)