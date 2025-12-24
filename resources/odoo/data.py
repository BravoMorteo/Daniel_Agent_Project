import xmlrpc.client
from datetime import datetime, timedelta, timezone
from dateutil import parser
from collections import defaultdict
from zoneinfo import ZoneInfo
import xmlrpc.client as xmlrpclib
from datetime import datetime, timedelta
from collections import defaultdict
import json


def reparaciones():
    url = "https://pegasuscontrol.odoo.com"
    db = "pegasuscontrol-pegasuscontrol-10820611"
    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ Authentication failed")
        exit()

    env = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    try:
        # Obtener todas las reparaciones (excluyendo done y cancel)
        repairs = env.execute_kw(
            db,
            uid,
            password,
            "repair.order",
            "search_read",
            [[("state", "not in", ["done", "cancel"])]],
            {
                "fields": [
                    "id",
                    "name",
                    "user_id",
                    "state",
                    "create_date",
                    "write_date",
                    "priority",
                ]
            },
        )

        # Agrupar por usuario
        repairs_by_user = defaultdict(list)

        for repair in repairs:
            user_info = repair.get("user_id", [False, "Sin asignar"])
            user_name = (
                user_info[1]
                if user_info and isinstance(user_info, list)
                else "Sin asignar"
            )
            repairs_by_user[user_name].append(repair)

        # Mostrar resultados agrupados
        print("=== Reparaciones por Usuario ===\n")
        for user_name in sorted(repairs_by_user.keys()):
            user_repairs = repairs_by_user[user_name]
            print(f"👤 {user_name}: {len(user_repairs)} reparaciones")

    except xmlrpc.client.Fault as fault:
        print(f"❌ Error XML-RPC: {fault.faultCode} → {fault.faultString}")


def field_by_id_leads(type, id):

    if type == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"

    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ Authentication failed")
        exit()

    env = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # Obtener todas las reparaciones (excluyendo done y cancel)
    fields = env.execute_kw(
        db,
        uid,
        password,
        "crm.lead",
        "search_read",
        [[("id", "=", id)]],  # <-- aquí pones el ID  (4)27323
        {
            "fields": [
                "id",
                "active",
                "company_id",
                "contact_name",
                "create_date",
                "date_conversion",
                "name",
                "probability",
                "user_id",
                "stage_id",
                "state_id",
                "type",
                "partner_id",
                "partner_name",
                "phone",
                "email_from",
                "order_ids",
            ],
            "limit": 1,  # opcional, porque un ID nunca se repite
        },
    )

    print(json.dumps(fields, indent=4, sort_keys=True))


def field_by_id_sale_order(type, id):
    if type == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"
    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ Authentication failed")
        return

    env = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    # 1️⃣ Leer la orden de venta
    sale_orders = env.execute_kw(
        db,
        uid,
        password,
        "sale.order",
        "search_read",
        [[("id", "=", id)]],
        {
            "fields": [
                "id",
                "name",
                "partner_id",
                "order_line",  # 👈 CLAVE
            ],
            "limit": 1,
        },
    )

    if not sale_orders:
        print("❌ No se encontró la orden")
        return

    sale_order = sale_orders[0]
    order_line_ids = sale_order["order_line"]

    # 2️⃣ Leer las líneas para obtener los productos
    lines = env.execute_kw(
        db,
        uid,
        password,
        "sale.order.line",
        "read",
        [order_line_ids],
        {"fields": ["product_id", "product_uom_qty", "price_unit"]},
    )

    # 3️⃣ Extraer solo los IDs de productos
    product_ids = [line["product_id"][0] for line in lines if line["product_id"]]

    resultado = {
        "sale_order_id": sale_order["id"],
        "sale_order_name": sale_order["name"],
        "product_ids": product_ids,
        "lines": lines,
    }

    print(json.dumps(resultado, indent=4, ensure_ascii=False))


# crea una funcion para buscar en res.partner por el campo email
def search_partner_by_email(type, email):
    if type == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"
    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})

    if not uid:
        print("❌ Authentication failed")
        return

    env = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    email_lower = email.lower()
    partners = env.execute_kw(
        db,
        uid,
        password,
        "res.partner",
        "search_read",
        [[("email", "=", email_lower)]],
        {
            "fields": [
                "id",
                "name",
                "email",
                "phone",
                "mobile",
                "street",
                "city",
                "country_id",
                "create_date",
            ],
            "limit": 10,
        },
    )

    print(json.dumps(partners, indent=4, ensure_ascii=False))


# crea una funcion que retorne a los usuarios con menos oportunidades asignadas
def get_salesperson_with_least_opportunities(env_type: str) -> int | None:
    if env_type == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"

    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("❌ Authentication failed")
        return None

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

    teams = models.execute_kw(
        db,
        uid,
        password,
        "crm.team",
        "search_read",
        [[("id", "in", [14])]],
        {"fields": ["member_ids"]},
    )

    members_ids = set()

    for team in teams:
        members_ids.update(team.get("member_ids", []))

    members_ids = list(members_ids)

    print(f"Miembros del equipo de ventas: {members_ids}")
    if not members_ids:
        print("⚠️ No hay miembros en el equipo de ventas")
        return None

    # 1️⃣
    leads = models.execute_kw(
        db,
        uid,
        password,
        "crm.lead",
        "search_read",
        [
            [
                ("stage_id", "in", [1, 2, 10, 3]),
                ("active", "=", True),
                ("type", "=", "opportunity"),
            ]
        ],
        {"fields": ["user_id"]},
    )

    # Agrupar por usuario
    opportunities_by_user = defaultdict(int)

    # 3️⃣ Contar oportunidades activas por vendedor
    for lead in leads:
        user_info = lead.get("user_id")
        if user_info and user_info[0] not in members_ids:
            continue
        if not user_info:
            continue
        user_id = user_info[0]
        user_name = user_info[1]
        if user_id not in opportunities_by_user:
            opportunities_by_user[user_id] = {
                "name": user_name,
                "count": 0,
            }
        opportunities_by_user[user_id]["count"] += 1

    if not opportunities_by_user:
        print("⚠️ No hay oportunidades asignadas")
        return None

    least_user_id = min(
        opportunities_by_user, key=lambda uid: opportunities_by_user[uid]["count"]
    )

    for uid_, data in opportunities_by_user.items():
        print(f"  {data['name']} (ID {uid_}): {data['count']}")

    print("\n🏆 Vendedor con menos oportunidades:")
    print(f"  ID: {least_user_id}")
    print(f"  Nombre: {opportunities_by_user[least_user_id]['name']}")
    print(f"  Oportunidades: {opportunities_by_user[least_user_id]['count']}")

    return least_user_id


# crea una funcion que me regrese los ids de los miembros de un equipo de ventas
def get_sales_team_member_ids(env_type: str, team_name) -> list[int]:
    if env_type == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"

    username = "laria@pegasus.com.mx"
    password = "Pegasus2024."

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
    uid = common.authenticate(db, username, password, {})
    if not uid:
        print("❌ Authentication failed")
        return []
    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")
    # Buscar el equipo de ventas por nombre
    teams = models.execute_kw(
        db,
        uid,
        password,
        "crm.team",
        "search_read",
        [[("id", "=", 1)]],
        {"fields": ["member_ids"]},
    )
    if not teams:
        print(f"⚠️ No se encontró el equipo de ventas con nombre '{team_name}'")
        return []

    member_ids = teams[0].get("member_ids", [])


def validate_pricelist(env="dev", pricelist_id=82):
    """
    Valida el modelo product.pricelist y muestra los items de precios configurados.

    Args:
        env: "prod" o "dev"
        pricelist_id: ID de la lista de precios (default: 82)
    """
    if env == "prod":
        url = "https://pegasuscontrol.odoo.com"
        db = "pegasuscontrol-pegasuscontrol-10820611"
        username = "laria@pegasus.com.mx"
        password = "Pegasus2024."
        api_key = "Pegasus2024."
    else:
        url = "https://pegasuscontrol-dev18-25468489.dev.odoo.com"
        db = "pegasuscontrol-dev18-25468489"
        username = "laria@pegasus.com.mx"
        password = "Pegasus2024."
        api_key = "Pegasus2024."

    print(f"\n{'='*100}")
    print(f"VALIDANDO PRICELIST - Ambiente: {env.upper()}")
    print(f"{'='*100}\n")

    common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common", allow_none=True)
    # Usar api_key si es dev, password si es prod
    auth = api_key if env == "dev" else password
    uid = common.authenticate(db, username, auth, {})

    if not uid:
        print("❌ Authentication failed")
        return

    models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object", allow_none=True)

    # Leer la pricelist
    pricelist = models.execute_kw(
        db,
        uid,
        auth,
        "product.pricelist",
        "read",
        [[pricelist_id]],
        {
            "fields": [
                "id",
                "name",
                "active",
                "currency_id",
                "item_ids",
                "company_id",
            ]
        },
    )

    if not pricelist:
        print(f"❌ No se encontró pricelist con ID {pricelist_id}")
        return

    pricelist = pricelist[0]
    print(f"📋 Pricelist encontrada:")
    print(f"   ID: {pricelist['id']}")
    print(f"   Nombre: {pricelist['name']}")
    print(f"   Activa: {pricelist['active']}")
    print(f"   Moneda: {pricelist.get('currency_id', 'N/A')}")
    print(f"   Política de descuento: {pricelist.get('discount_policy', 'N/A')}")
    print(f"   Compañía: {pricelist.get('company_id', 'N/A')}")

    item_ids = pricelist.get("item_ids", [])
    print(f"\n📦 Cantidad de items configurados: {len(item_ids)}")

    if item_ids:
        print(f"\n{'='*100}")
        print("ITEMS DE PRECIOS (primeros 20)")
        print(f"{'='*100}\n")

        # Leer los primeros 20 items para no saturar
        items = models.execute_kw(
            db,
            uid,
            auth,
            "product.pricelist.item",
            "read",
            [item_ids[:20]],
            {
                "fields": [
                    "id",
                    "product_tmpl_id",
                    "product_id",
                    "min_quantity",
                    "fixed_price",
                    "percent_price",
                    "price_discount",
                    "price_surcharge",
                    "compute_price",
                    "applied_on",
                ]
            },
        )

        print(
            f"{'ID':<8} {'Tipo':<20} {'Producto':<40} {'Precio Fijo':<15} {'% Desc':<10}"
        )
        print("-" * 100)

        for item in items:
            item_id = item["id"]
            applied_on = item.get("applied_on", "N/A")
            compute_price = item.get("compute_price", "N/A")

            # Determinar el producto
            product_name = "N/A"
            if item.get("product_id"):
                product_name = (
                    item["product_id"][1]
                    if isinstance(item["product_id"], list)
                    else str(item["product_id"])
                )
            elif item.get("product_tmpl_id"):
                product_name = (
                    item["product_tmpl_id"][1]
                    if isinstance(item["product_tmpl_id"], list)
                    else str(item["product_tmpl_id"])
                )

            fixed_price = item.get("fixed_price", 0)
            percent_price = item.get("percent_price", 0)
            price_discount = item.get("price_discount", 0)

            print(
                f"{item_id:<8} {compute_price:<20} {product_name[:38]:<40} ${fixed_price:<14.2f} {price_discount:<10.1f}"
            )

        print("-" * 100)

        # Buscar robots específicamente
        print(f"\n{'='*100}")
        print("BUSCANDO ITEMS DE ROBOTS EN LA PRICELIST")
        print(f"{'='*100}\n")

        robot_items = []
        for item_id in item_ids:
            item = models.execute_kw(
                db,
                uid,
                auth,
                "product.pricelist.item",
                "read",
                [[item_id]],
                {"fields": ["id", "product_id", "fixed_price", "compute_price"]},
            )[0]

            if item.get("product_id"):
                product_id = (
                    item["product_id"][0]
                    if isinstance(item["product_id"], list)
                    else item["product_id"]
                )
                product_name = (
                    item["product_id"][1]
                    if isinstance(item["product_id"], list)
                    else "N/A"
                )

                # Filtrar robots
                if any(
                    keyword in product_name.lower()
                    for keyword in ["robot", "cc1", "swiftbot", "pudu", "kettybot"]
                ):
                    robot_items.append(
                        {
                            "id": item["id"],
                            "product_id": product_id,
                            "product_name": product_name,
                            "fixed_price": item.get("fixed_price", 0),
                            "compute_price": item.get("compute_price", "N/A"),
                        }
                    )

        if robot_items:
            print(f"✅ Encontrados {len(robot_items)} robots en la pricelist:\n")
            print(
                f"{'Item ID':<10} {'Producto ID':<12} {'Precio':<15} {'Producto':<50}"
            )
            print("-" * 100)
            for robot in robot_items:
                print(
                    f"{robot['id']:<10} {robot['product_id']:<12} ${robot['fixed_price']:<14.2f} {robot['product_name'][:48]}"
                )
            print("-" * 100)
        else:
            print("⚠️ No se encontraron robots en la pricelist")

    print(f"\n{'='*100}\n")


if __name__ == "__main__":

    # reparaciones()
    # field_by_id_sale_order()
    search_partner_by_email("dev", "castillo@gmail.com")
    print(
        "\n*******************************menos oportunidades****************************************\n"
    )
    get_salesperson_with_least_opportunities("dev")
    field_by_id_leads("dev", 27439)
    print("\n***********************************************************************\n")
    # get_sales_team_member_ids("dev", "Ventas")

    # Validar pricelist
    # validate_pricelist("dev", 82)
