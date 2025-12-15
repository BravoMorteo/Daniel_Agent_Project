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


def field_by_id_leads():
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
        [[("id", "=", 27330)]],  # <-- aquí pones el ID  (4)27323
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
                "order_ids",
            ],
            "limit": 1,  # opcional, porque un ID nunca se repite
        },
    )

    print(json.dumps(fields, indent=4, sort_keys=True))


if __name__ == "__main__":

    # reparaciones()
    field_by_id_leads()
