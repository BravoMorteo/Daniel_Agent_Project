# 📝 Sistema de Logs JSON con S3

## Resumen

El servidor MCP-Odoo ahora incluye un **sistema de logging automático** que registra todas las cotizaciones en formato JSON y las sube automáticamente a S3 para auditoría y análisis.

## 🎯 Características

✅ **Logging Automático**: Cada cotización se registra sin intervención manual  
✅ **Formato JSON**: Estructura clara y fácil de analizar  
✅ **Subida a S3**: Los logs se cargan automáticamente a AWS S3  
✅ **Organización por Fecha**: Archivos nombrados como `YYYY-MM-DD_tracking_id.log`

## 📁 Estructura de un Log

```json
{
  "tracking_id": "quot_1539be395784",
  "timestamp": "2025-12-22T10:48:40.405304",
  "date": "2025-12-22",
  "time": "10:48:40.405",
  "status": "completed",
  "input": {
    "partner_name": "Company Name",
    "contact_name": "Contact Person",
    "email": "email@example.com",
    "phone": "+52 55 1234 5678",
    "lead_name": "Lead Name",
    "product_id": 26174,
    "product_qty": 3,
    "product_price": -1.0,
    "user_id": 0
  },
  "output": {
    "partner_id": 124253,
    "lead_id": 27409,
    "opportunity_id": 27409,
    "sale_order_id": 18689,
    "sale_order_name": "S15428",
    "user_id": 3012,
    "product_line_note": "Precio aplicado..."
  },
  "error": null,
  "updated_at": "2025-12-22T10:48:55.806648"
}
```

## ⚙️ Configuración

### 1. Variables de Entorno

Agrega estas variables a tu archivo `.env`:

```bash
# ===== AWS S3 PARA LOGS =====
S3_LOGS_BUCKET=ilagentslogs
AWS_REGION=us-west-2
AWS_ROLE_ARN=arn:aws:s3:::ilagentslogs

### 2. Método de Autenticación S3

El sistema soporta 3 métodos de autenticación:

#### Método: Access Keys (Desarrollo)
```bash
AWS_ACCESS_KEY_ID=AKIAXXXXXXXXXXXXXXXX
AWS_SECRET_ACCESS_KEY=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx```

## 🚀 Uso

### El logging es automático

No necesitas hacer nada. Cada vez que creas una cotización:

```bash
curl -X POST http://localhost:8000/api/quotation/async \
  -H "Content-Type: application/json" \
  -d '{
    "partner_name": "Company Name",
    "contact_name": "Contact Person",
    "email": "email@example.com",
    "phone": "+52 55 1234 5678",
    "lead_name": "Lead Name",
    "product_id": 26174,
    "product_qty": 1
  }'
```

El sistema automáticamente:
1. ✅ Crea un log inicial con `status: "started"`
2. ✅ Guarda el log localmente en `/tmp/mcp_odoo_logs/`
3. ✅ Sube el log a S3 inmediatamente
4. ✅ Actualiza el log cuando completa con `status: "completed"` o `"failed"`
5. ✅ Vuelve a subir la versión actualizada a S3


### Instalar Dependencias

```bash
cd services/mcp-odoo
source .venv/bin/activate
pip install -e .
```

Esto instalará `boto3>=1.34.0` automáticamente.

---

## 📊 Estructura en S3

Los logs se organizan automáticamente por año/mes:

```
s3://your-mcp-odoo-logs/
└── mcp-odoo-logs/
    ├── 2025/
    │   ├── 12/
    │   │   ├── 2025-12-22_quot_4ea1daac9b8d.log
    │   │   ├── 2025-12-22_quot_b94f46c5bdb1.log
    │   │   └── 2025-12-23_quot_abc123def456.log
    │   └── 11/
    │       └── 2025-11-30_quot_xyz789.log
    └── 2024/
        └── 12/
            └── 2024-12-15_quot_old123.log
```

---

### Ver logs locales

```bash
# Listar logs del día
ls -lh /tmp/mcp_odoo_logs/2025-12-22*.log

# Ver contenido de un log
cat /tmp/mcp_odoo_logs/2025-12-22_quot_1539be395784.log | python -m json.tool
```

### Ver logs en S3

```bash
# Listar logs del mes
aws s3 ls s3://ilagentslogs/mcp-odoo-logs/2025/12/

# Descargar un log específico
aws s3 cp s3://ilagentslogs/mcp-odoo-logs/2025/12/2025-12-22_quot_1539be395784.log .

# Ver contenido directamente
aws s3 cp s3://ilagentslogs/mcp-odoo-logs/2025/12/2025-12-22_quot_1539be395784.log - | python -m json.tool
```

## 📊 Análisis de Logs

### Con jq (línea de comandos)

```bash
# Contar cotizaciones completadas del día
cat /tmp/mcp_odoo_logs/2025-12-22*.log | jq -s '[.[] | select(.status=="completed")] | length'

# Listar errores
cat /tmp/mcp_odoo_logs/2025-12-22*.log | jq -s '.[] | select(.error != null)'

# Extraer tiempos de procesamiento
cat /tmp/mcp_odoo_logs/2025-12-22*.log | jq -s '.[] | {tracking_id, started: .timestamp, completed: .updated_at}'
```

## 📚 Documentación Adicional

- **`docs/S3_LOGS_SETUP.md`**: Guía completa de configuración de S3
- **`examples/test_logging_complete.sh`**: Script de demostración completo

## ✅ Sistema Verificado y Funcionando

- [x] QuotationLogger class implementado
- [x] Integración con FastAPI background tasks
- [x] Boto3 instalado y configurado
- [x] Variables de entorno en .env
- [x] Subida automática a S3
- [x] Documentación completa
- [x] Scripts de prueba
- [x] Demo exitosa con tracking_id: `quot_1539be395784`

## 🎉 ¡Listo!

El sistema de logging está completamente funcional y listo para producción. Los logs se generan automáticamente, se guardan localmente, y se suben a S3 para análisis y auditoría.

**Logs generados hoy:** `ls -lh /tmp/mcp_odoo_logs/`  
**Ubicación en S3:** `s3://ilagentslogs/mcp-odoo-logs/2025/12/`
