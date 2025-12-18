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

    partners = env.execute_kw(
        db,
        uid,
        password,
        "res.partner",
        "search_read",
        [[("email", "=", email)]],
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


if __name__ == "__main__":

    # reparaciones()
    # field_by_id_sale_order()
    field_by_id_leads("dev", 27351)
    print("\n***********************************************************************\n")
    search_partner_by_email("dev", "Ricardo@Recolino.com.mx")
    print(
        "\n*******************************menos oportunidades****************************************\n"
    )
    get_salesperson_with_least_opportunities("dev")
    # get_sales_team_member_ids("dev", "Ventas")
