
import os
import sys
import xmlrpc.client

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

class DevOdooCRMClient:
    def __init__(self):
        # Fallback logic matcher
        env_url = os.environ.get("DEV_ODOO_URL") or os.environ.get("ODOO_URL")
        env_db = os.environ.get("DEV_ODOO_DB") or os.environ.get("ODOO_DB")
        env_user = os.environ.get("DEV_ODOO_LOGIN") or os.environ.get("ODOO_LOGIN")
        env_key = os.environ.get("DEV_ODOO_API_KEY") or os.environ.get("ODOO_API_KEY") or os.environ.get("ODOO_PASSWORD")
        
        self.url = (env_url or "https://pegasuscontrol-dev18-25468489.dev.odoo.com").rstrip("/")
        self.db = env_db or "pegasuscontrol-dev18-25468489"
        self.username = env_user
        self.password = env_key

        if not self.username:
            raise ValueError("Missing ODOO_LOGIN")

        self.common = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/common", allow_none=True)
        self.models = xmlrpc.client.ServerProxy(f"{self.url}/xmlrpc/2/object", allow_none=True)
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

    def execute_kw(self, model, method, args=None, kwargs=None):
        return self.models.execute_kw(self.db, self.uid, self.password, model, method, args or [], kwargs or {})

    def create(self, model, values):
        return self.execute_kw(model, "create", [values])
    
    def read(self, model, id, fields=None):
         res = self.execute_kw(model, "read", [[id]], {"fields": fields or []})
         return res[0] if res else {}

def create_quotation():
    client = DevOdooCRMClient()
    print("Client initialized.")

    # 1. Partner
    partner_id = client.create("res.partner", {
        "name": "Test Client Ketty",
        "email": "test.ketty@example.com",
        "phone": "5555555555"
    })
    print(f"Partner created: {partner_id}")

    # 2. Lead
    lead_id = client.create("crm.lead", {
        "name": "Test Quotation Two KettyBots",
        "partner_id": partner_id,
        "type": "opportunity"
    })
    print(f"Lead created: {lead_id}")

    # 3. Sale Order
    so_id = client.create("sale.order", {
        "partner_id": partner_id,
        "opportunity_id": lead_id,
        "state": "draft"
    })
    so_name = client.read("sale.order", so_id, ["name"]).get("name")
    print(f"Sale Order created: {so_name} (ID: {so_id})")

    # 4. Add Products
    # Product ID 26153 (KettyBot), Qty 2
    # Price: we can let it imply or force it. Let's force 120.0 as seen in previous verification for consistency
    product_id = 26153
    qty = 2.0
    
    line_id = client.create("sale.order.line", {
        "order_id": so_id,
        "product_id": product_id,
        "product_uom_qty": qty,
        # "price_unit": 120.0 # Optional
    })
    print(f"Added Product {product_id} x{qty} to line {line_id}")
    
    print("\nSUCCESS: Quotation created.")
    print(f"Tracking Info: Lead ID {lead_id}, Sale Order {so_name}")

if __name__ == "__main__":
    create_quotation()
