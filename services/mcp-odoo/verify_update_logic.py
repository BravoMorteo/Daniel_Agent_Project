
import os
import sys
import xmlrpc.client
from datetime import datetime

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Load .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not found, assuming env vars are set or irrelevant if using hardcoded credentials (not recommended)")

# --- EMBEDDED CLASS TO AVOID CIRCULAR IMPORT ---
class DevOdooCRMClient:
    """
    Cliente Odoo específico para el ambiente de DESARROLLO (CRM/Cotizaciones).
    Se conecta a: pegasuscontrol-dev18-25468489.dev.odoo.com
    """


    def __init__(self):
        # Configuración específica para DESARROLLO
        # Intentar leer variables DEV_, si no existen, usar ODOO_ (fallback)
        
        env_url = os.environ.get("DEV_ODOO_URL") or os.environ.get("ODOO_URL")
        env_db = os.environ.get("DEV_ODOO_DB") or os.environ.get("ODOO_DB")
        env_user = os.environ.get("DEV_ODOO_LOGIN") or os.environ.get("ODOO_LOGIN")
        env_key = os.environ.get("DEV_ODOO_API_KEY") or os.environ.get("ODOO_API_KEY") or os.environ.get("ODOO_PASSWORD")
        
        self.url = env_url.rstrip("/")
        self.db = env_db 
        self.username = env_user
        self.password = env_key

        if not self.username or not self.password:
            print(f"DEBUG: Found credentials - User: {self.username}, Key: {'*' * (len(self.password) if self.password else 0)}")
            raise ValueError(
                "Faltan credenciales ODOO_LOGIN/ODOO_API_KEY en .env"
            )

        # Conexión XML-RPC a desarrollo con allow_none=True para manejar valores None
        self.common = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/common", allow_none=True
        )
        self.models = xmlrpc.client.ServerProxy(
            f"{self.url}/xmlrpc/2/object", allow_none=True
        )

        # Autenticación
        self.uid = self.common.authenticate(self.db, self.username, self.password, {})

        if not self.uid:
            raise ValueError("No se pudo autenticar en el ambiente de desarrollo")

    def execute_kw(self, model: str, method: str, args=None, kwargs=None):
        """Ejecuta un método en el modelo especificado."""
        args = args or []
        kwargs = kwargs or {}
        return self.models.execute_kw(
            self.db, self.uid, self.password, model, method, args, kwargs
        )

    def search_read(
        self, model: str, domain: list, fields: list, limit: int = 1
    ) -> list:
        """Busca y lee registros."""
        return self.execute_kw(
            model, "search_read", [domain], {"fields": fields, "limit": limit}
        )

    def create(self, model: str, values: dict) -> int:
        """Crea un nuevo registro."""
        return self.execute_kw(model, "create", [values])

    def write(self, model: str, record_id: int, values: dict) -> bool:
        """Actualiza un registro existente."""
        return self.execute_kw(model, "write", [[record_id], values])

    def read(self, model: str, record_id: int, fields: list = None) -> dict:
        """Lee un registro por ID."""
        fields = fields or []
        result = self.execute_kw(model, "read", [[record_id]], {"fields": fields})
        return result[0] if result else {}

    def dev_update_lead_quotation_manual(self, lead_id, description=None, link_quotation_id=None, unlink_other_quotations=False, products=None, replace_products=True):
        """
        Manually executes the logic of dev_update_lead_quotation without the MCP wrapper.
        """
        print(f"--- Updating Lead {lead_id} ---")
        
        # 1. Update Lead
        if description:
            print(f"Updating description to: {description}")
            self.write("crm.lead", lead_id, {"description": description})

        # 1.5 Link Quotation
        if link_quotation_id:
            print(f"Linking Quotation {link_quotation_id} to Lead {lead_id}...")
            so_check = self.read("sale.order", link_quotation_id, ["id", "name"])
            if so_check:
                if unlink_other_quotations:
                    print("Unlinking other quotations...")
                    other_sos = self.search_read(
                        "sale.order",
                        [("opportunity_id", "=", lead_id), ("id", "!=", link_quotation_id)],
                        ["id", "name"]
                    )
                    for other in other_sos:
                        self.write("sale.order", other["id"], {"opportunity_id": False})
                        print(f"  > Unlinked Sale Order {other['id']} ({other['name']})")

                self.write("sale.order", link_quotation_id, {"opportunity_id": lead_id})
                print(f"✅ Linked Sale Order {link_quotation_id} ({so_check.get('name')})")
            else:
                print(f"⚠️ Sale Order {link_quotation_id} not found.")

        # 2. Find Linked Sale Order
        sale_orders = self.search_read(
            "sale.order",
            [("opportunity_id", "=", lead_id), ("state", "in", ["draft", "sent"])],
            ["id", "name"]
        )

        if not sale_orders:
            print("❌ No active Sale Order found for this lead.")
            return

        sale_order = sale_orders[0]
        so_id = sale_order["id"]
        print(f"Found Sale Order: {sale_order['name']} (ID: {so_id})")

        if products:
            if replace_products:
                print("Clearing existing lines...")
                self.write("sale.order", so_id, {"order_line": [(5, 0, 0)]})

            for prod in products:
                pid = prod.get("product_id")
                qty = prod.get("qty", 1.0)
                price = prod.get("price", -1.0)
                
                line_values = {
                    "order_id": so_id,
                    "product_id": pid,
                    "product_uom_qty": qty,
                }

                # Price logic
                if price > 0:
                    line_values["price_unit"] = price
                else:
                    try:
                        p_data = self.read("product.product", pid, ["list_price"])
                        if p_data:
                            line_values["price_unit"] = p_data.get("list_price", 0.0)
                    except:
                        pass
                
                print(f"Adding Product {pid} x{qty} @ {line_values.get('price_unit')}...")
                lid = self.create("sale.order.line", line_values)
                
                # Force Price
                if price > 0:
                     self.write("sale.order.line", lid, {"price_unit": price})
                     print(f"  > Forced price to {price}")

        print("--- Update Complete ---")

if __name__ == "__main__":
    client = DevOdooCRMClient()
    
    # --- CONFIGURATION SECTION ---
    # EDIT THESE VALUES TO UPDATE A LEAD MANUALLY
    LEAD_ID = 31713
    DESCRIPTION = "Manual Update via Script 2"
    LINK_QUOTATION_ID = 21668  # Set to an integer ID to link, or None
    UNLINK_OTHER_QUOTATIONS = True # Set to True to unlink other quotations
    PRODUCTS = [
        # {"product_id": 26153, "qty": 1, "price": 120.0},
        # {"product_id": 24049, "qty": 1}
    ]
    REPLACE_PRODUCTS = False # Set to True to wipe existing lines
    # -----------------------------

    client.dev_update_lead_quotation_manual(
        lead_id=LEAD_ID,
        description=DESCRIPTION,
        link_quotation_id=LINK_QUOTATION_ID,
        unlink_other_quotations=UNLINK_OTHER_QUOTATIONS,
        products=PRODUCTS,
        replace_products=REPLACE_PRODUCTS
    )
