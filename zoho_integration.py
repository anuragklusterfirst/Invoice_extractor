# zoho_integration.py
import os
import requests
import json

ZOHO_CLIENT_ID = os.environ.get("ZOHO_CLIENT_ID")
ZOHO_CLIENT_SECRET = os.environ.get("ZOHO_CLIENT_SECRET")
ZOHO_REFRESH_TOKEN = os.environ.get("ZOHO_REFRESH_TOKEN")
ZOHO_ORG_ID = os.environ.get("ZOHO_ORG_ID")  # Your organization ID from Zoho

BASE_URL = "https://invoice.zoho.com/api/v3"

def get_access_token():
    url = "https://accounts.zoho.com/oauth/v2/token"
    data = {
        "refresh_token": ZOHO_REFRESH_TOKEN,
        "client_id": ZOHO_CLIENT_ID,
        "client_secret": ZOHO_CLIENT_SECRET,
        "grant_type": "refresh_token"
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()["access_token"]

def zoho_headers():
    return {
        "Authorization": f"Zoho-oauthtoken {get_access_token()}",
        "X-com-zoho-invoice-organizationid": ZOHO_ORG_ID,
        "Content-Type": "application/json"
    }

def create_invoice(invoice_data: dict):
    """
    Create an invoice on Zoho using the extracted invoice_data dict.
    Map your invoice_data keys to Zoho's API format here.
    """
    url = f"{BASE_URL}/invoices"
    
    # Basic mapping example, adjust according to your extracted data structure and zoho API requirements
    payload = {
        "customer_name": invoice_data.get("User Name", "Unknown"),
        "payment_terms": 0,  # Customize or parse appropriately
        "invoice_number": invoice_data.get("Invoice Number", ""),
        "date": invoice_data.get("Invoice Date", ""),  # You may need to parse/format date
        "due_date": invoice_data.get("Due Date", ""),
        "line_items": [],
        "taxes": [],
        "notes": "Created from extracted invoice data"
    }
    
    product_details = invoice_data.get("Product Details", [])
    if isinstance(product_details, list):
        for product in product_details:
            item = {
                "name": product.get("name", ""),
                "rate": float(product.get("price", 0) or 0),
                "quantity": float(product.get("quantity", 1) or 1),
                "description": "",
            }
            payload["line_items"].append(item)
    
    response = requests.post(url, headers=zoho_headers(), data=json.dumps(payload))
    if response.status_code == 201:
        return True, response.json()
    else:
        return False, response.text

def get_invoices():
    """
    Retrieve invoices from Zoho.
    """
    url = f"{BASE_URL}/invoices"
    response = requests.get(url, headers=zoho_headers())
    if response.status_code == 200:
        return True, response.json()
    else:
        return False, response.text
 