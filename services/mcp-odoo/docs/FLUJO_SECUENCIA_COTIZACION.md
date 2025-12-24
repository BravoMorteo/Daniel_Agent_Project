# 🔄 Flujo de Secuencia: "Haz una Cotización..."

**Caso de Uso:** Usuario dice "Haz una cotización para Robot PUDU, cliente Acme Corp"  
**Fecha:** Diciembre 2025  
**Sistema:** Servidor Híbrido FastAPI + MCP

---

## 📋 Diagrama de Secuencia Completo

```
┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────────┐  ┌─────────┐  ┌──────┐
│ Usuario │  │   LLM    │  │  MCP    │  │ FastAPI  │  │  Tool   │  │ OdooAPI  │  │TaskMgr/ │  │  S3  │
│(Claude) │  │(Cerebro) │  │Protocol │  │  Server  │  │ (crm.py)│  │(XML-RPC) │  │ Logger  │  │Bucket│
└────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬────┘  └────┬─────┘  └────┬────┘  └──┬───┘
     │            │              │             │             │             │             │          │
     │                                                                                              │
     │  1. "Haz una cotización..."                                                                 │
     ├───────────►│                                                                                │
     │            │                                                                                │
     │            │  2. Analiza contexto                                                          │
     │            │     - Identifica: crear cotización                                            │
     │            │     - Extrae: partner, email, producto                                        │
     │            │     - Decide: usar dev_create_quotation                                       │
     │            │                                                                                │
     │            │  3. Llama tool via MCP                                                        │
     │            ├──────────────►│                                                                │
     │            │                │  4. POST /mcp/messages                                        │
     │            │                │     (JSON-RPC)                                                │
     │            │                ├────────────────►│                                             │
     │            │                │                 │                                             │
     │            │                │                 │  5. Enruta a tool handler                   │
     │            │                │                 │     app.mount("/mcp", mcp.sse_app())        │
     │            │                │                 ├────────────────►│                           │
     │            │                │                 │                 │                           │
     │            │                │                 │                 │  6. dev_create_quotation()│
     │            │                │                 │                 │     • Genera tracking_id  │
     │            │                │                 │                 │     • quot_abc123def456   │
     │            │                │                 │                 │                           │
     │            │                │                 │                 │  7. Crea tarea            │
     │            │                │                 │                 ├──────────────────────────►│
     │            │                │                 │                 │   task_manager.create()   │
     │            │                │                 │                 │◄──────────────────────────┤
     │            │                │                 │                 │   Task created (queued)   │
     │            │                │                 │                 │                           │
     │            │                │                 │                 │  8. Log inicial           │
     │            │                │                 │                 ├──────────────────────────►│
     │            │                │                 │                 │   logger.log_quotation()  │
     │            │                │                 │                 │                         ──┼──►│
     │            │                │                 │                 │◄──────────────────────────┤   │
     │            │                │                 │                 │   Log saved: /tmp/*.log   │   │
     │            │                │                 │                 │                           │   │
     │            │                │                 │                 │  9. Lanza background      │   │
     │            │                │                 │                 │     thread                │   │
     │            │                │                 │                 │     Thread(              │   │
     │            │                │                 │                 │       target=process_bg, │   │
     │            │                │                 │                 │       args=(tracking_id) │   │
     │            │                │                 │                 │     ).start()            │   │
     │            │                │                 │                 │                           │   │
     │            │                │                 │  10. Respuesta inmediata                    │   │
     │            │                │                 │◄────────────────┤   (no espera Odoo)        │   │
     │            │                │  11. JSON-RPC   │                 │   {"tracking_id": "...",  │   │
     │            │                │     Response    │                 │    "status": "queued"}    │   │
     │            │◄────────────────┤                 │                 │                           │   │
     │            │  {"tracking_id":"quot_abc123"}   │                 │                           │   │
     │◄───────────┤                 │                 │                 │                           │   │
     │  "Cotización│                │                 │                 │                           │   │
     │  iniciada..." │                │                 │                 │                           │   │
     │            │                 │                 │                 │                           │   │
     │                                                                                              │   │
     │  ═══════════════════════════ AQUÍ TERMINA LA RESPUESTA AL USUARIO ═══════════════════════  │   │
     │  ═══════════════════════════ BACKGROUND PROCESSING INICIA ═══════════════════════════════  │   │
     │                                                                                              │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │           [BACKGROUND THREAD]             │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  12. Update task          │   │
     │                                 │                 │                 ├──────────────────────────►│   │
     │                                 │                 │                 │   status = "processing"   │   │
     │                                 │                 │                 │◄──────────────────────────┤   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  13. Conecta a Odoo       │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   OdooClient()│            │   │
     │                                 │                 │                 │   authenticate()│         │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   uid = 123  │            │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  14. Get/Create Partner   │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   search('res.partner')   │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   partner_id = 124258    │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  15. Update progress      │   │
     │                                 │                 │                 ├──────────────────────────►│   │
     │                                 │                 │                 │   "Creando lead..."       │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  16. Create Lead          │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   create('crm.lead')      │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   lead_id = 27414        │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  17. Convert to Opportunity│  │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   write({'type':'opportunity'})│
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   opportunity_id = 27414 │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  18. Update progress      │   │
     │                                 │                 │                 ├──────────────────────────►│   │
     │                                 │                 │                 │   "Creando orden..."      │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  19. Create Sale Order    │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   create('sale.order')    │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   order_id = 18694       │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  20. Get Product Price    │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   read('product.product') │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   price = $15,950.00     │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  21. Add Product Line     │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   create('sale.order.line')│  │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   line_id = 47587        │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  22. Get Order Name       │   │
     │                                 │                 │                 ├────────────►│            │   │
     │                                 │                 │                 │   read(['name'])          │   │
     │                                 │                 │                 │◄────────────┤            │   │
     │                                 │                 │                 │   name = "S15433"        │   │
     │                                 │                 │                 │              │            │   │
     │                                 │                 │                 │  23. Complete Task        │   │
     │                                 │                 │                 ├──────────────────────────►│   │
     │                                 │                 │                 │   task_manager.complete()│   │
     │                                 │                 │                 │   status = "completed"   │   │
     │                                 │                 │                 │   result = {...}         │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  24. Update Log           │   │
     │                                 │                 │                 ├──────────────────────────►│   │
     │                                 │                 │                 │   logger.update_log()    │   │
     │                                 │                 │                 │                         ──┼──►│
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  25. Upload to S3         │   │
     │                                 │                 │                 │                           ├──►│
     │                                 │                 │                 │   s3.upload_file()        │   │
     │                                 │                 │                 │   s3://ilagentslogs/...   │   │
     │                                 │                 │                 │                           │   │
     │                                 │                 │                 │  26. Background Complete  │   │
     │                                 │                 │                 │   (Thread termina)        │   │
     │                                 │                 │                 │                           │   │
     │                                                                                                 │   │
     │  ═══════════════════════════ USUARIO CONSULTA ESTADO (OPCIONAL) ═════════════════════════════│   │
     │                                                                                                 │   │
     │  27. "¿Cuál es el estado?"                                                                     │   │
     ├───────────►│                                                                                   │   │
     │            │  28. dev_get_quotation_status()                                                   │   │
     │            ├──────────────►│                                                                   │   │
     │            │                │  29. POST /mcp/messages                                          │   │
     │            │                ├────────────────►│                                                │   │
     │            │                │                 │  30. Enruta a tool                             │   │
     │            │                │                 ├────────────────►│                              │   │
     │            │                │                 │                 │  31. Get Task                │   │
     │            │                │                 │                 ├──────────────────────────►   │   │
     │            │                │                 │                 │   task_manager.get_task()    │   │
     │            │                │                 │                 │◄──────────────────────────   │   │
     │            │                │                 │                 │   task.to_dict()             │   │
     │            │                │                 │◄────────────────┤                              │   │
     │            │                │  32. JSON Response                │                              │   │
     │            │◄────────────────┤                 │                 │                              │   │
     │◄───────────┤  {"status":"completed",          │                 │                              │   │
     │  "Cotización│   "result": {                    │                 │                              │   │
     │  completada!│     "sale_order_name": "S15433"  │                 │                              │   │
     │  S15433"    │   }}                             │                 │                              │   │
     │            │                 │                 │                 │                              │   │
```

---

## 🔍 Detalle de Cada Paso

### **Fase 1: Interacción Usuario → LLM (Pasos 1-2)**

**Paso 1: Usuario inicia conversación**
```
Usuario: "Haz una cotización para Robot PUDU, 
          cliente Acme Corp, email: acme@corp.com, 
          tel: +52 55 1234 5678"
```

**Paso 2: LLM analiza y decide**
```python
# El LLM (Claude) analiza:
- Intención: Crear cotización
- Entidades extraídas:
  * Producto: "Robot PUDU" → busca product_id
  * Cliente: "Acme Corp"
  * Email: "acme@corp.com"
  * Teléfono: "+52 55 1234 5678"

# Decisión: Usar tool "dev_create_quotation"
```

---

### **Fase 2: MCP Protocol (Pasos 3-5)**

**Paso 3: LLM → MCP Protocol**
```
Claude decide llamar a la tool via MCP
```

**Paso 4: JSON-RPC Request**
```json
POST http://localhost:8000/mcp/messages
Content-Type: application/json

{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "dev_create_quotation",
    "arguments": {
      "partner_name": "Acme Corp",
      "contact_name": "John Doe",
      "email": "acme@corp.com",
      "phone": "+52 55 1234 5678",
      "lead_name": "Cotización Robot PUDU",
      "product_id": 26174,
      "product_qty": 1,
      "product_price": -1,
      "user_id": 0
    }
  }
}
```

**Paso 5: FastAPI enruta a tool handler**
```python
# En server.py:
app.mount("/mcp", mcp.sse_app())

# FastMCP internamente:
# 1. Recibe POST /mcp/messages
# 2. Parsea JSON-RPC
# 3. Identifica tool: "dev_create_quotation"
# 4. Busca función registrada con @mcp.tool()
# 5. Ejecuta: tools/crm.py::dev_create_quotation()
```

---

### **Fase 3: Tool Execution (Pasos 6-11)**

**Paso 6: dev_create_quotation() comienza**
```python
# tools/crm.py

def dev_create_quotation(partner_name, email, ...):
    # 1. Genera tracking_id único
    tracking_id = f"quot_{uuid.uuid4().hex[:12]}"
    # → "quot_abc123def456"
    
    # 2. Crea objeto request
    request = QuotationRequest(
        partner_name=partner_name,
        email=email,
        ...
    )
```

**Paso 7: Crear tarea en TaskManager**
```python
    # 3. Registra tarea (in-memory)
    task_manager.create_task(tracking_id, request.dict())
    # TaskManager guarda:
    # {
    #   "tracking_id": "quot_abc123def456",
    #   "status": "queued",
    #   "created_at": "2025-12-22T15:30:00",
    #   "params": {...}
    # }
```

**Paso 8: Log inicial**
```python
    # 4. Log a archivo JSON
    quotation_logger.log_quotation(
        tracking_id, 
        request.dict(),
        status="queued"
    )
    # Crea: /tmp/mcp_odoo_logs/2025-12-22_quot_abc123def456.log
```

**Paso 9: Lanzar background thread**
```python
    # 5. Procesamiento asíncrono
    thread = threading.Thread(
        target=process_quotation_background,
        args=(tracking_id, request)
    )
    thread.start()  # ← NO espera, continúa inmediatamente
```

**Paso 10-11: Respuesta inmediata**
```python
    # 6. Retorna inmediatamente (SIN esperar Odoo)
    return {
        "tracking_id": "quot_abc123def456",
        "status": "queued",
        "message": "Cotización en proceso...",
        "estimated_time": "20-30 segundos",
        "check_status_with": "dev_get_quotation_status(...)"
    }
    # ← El usuario ve esto en ~50ms
```

---

### **Fase 4: Background Processing (Pasos 12-26)**

**IMPORTANTE:** Esta fase ocurre **EN PARALELO** mientras el usuario ya recibió respuesta.

**Paso 12: Actualizar estado a "processing"**
```python
# core/api.py::process_quotation_background()

def process_quotation_background(tracking_id, request):
    try:
        # 1. Cambiar estado
        task_manager.update_task(
            tracking_id,
            status="processing",
            progress="Conectando a Odoo..."
        )
```

**Paso 13: Conectar a Odoo**
```python
        # 2. Autenticación XML-RPC
        odoo = OdooClient()
        # odoo.authenticate() → uid = 2136
```

**Paso 14: Crear/buscar Partner**
```python
        # 3. Partner (cliente)
        task_manager.update_task(tracking_id, progress="Creando partner...")
        
        partner_id = odoo.get_or_create_partner(
            "Acme Corp",
            "acme@corp.com",
            "+52 55 1234 5678"
        )
        # Odoo busca por email, si no existe crea nuevo
        # → partner_id = 124258
```

**Paso 15-16: Crear Lead**
```python
        # 4. Lead (oportunidad inicial)
        task_manager.update_task(tracking_id, progress="Creando lead...")
        
        lead_id = odoo.create_lead(
            "Cotización Robot PUDU",
            partner_id
        )
        # → lead_id = 27414
```

**Paso 17: Convertir a Opportunity**
```python
        # 5. Convertir lead → opportunity
        opp_id = odoo.convert_to_opportunity(lead_id)
        # Actualiza: type = 'opportunity'
        # → opp_id = 27414 (mismo ID)
```

**Paso 18-19: Crear Sale Order**
```python
        # 6. Orden de venta
        task_manager.update_task(tracking_id, progress="Creando orden...")
        
        sale_order_id = odoo.create_sale_order(
            partner_id,
            user_id=None  # Asignación automática
        )
        # → sale_order_id = 18694
```

**Paso 20-21: Agregar producto**
```python
        # 7. Obtener precio de lista
        product = odoo.execute(
            'product.product', 'read',
            [26174],  # product_id
            ['list_price']
        )[0]
        price = product['list_price']  # → $15,950.00
        
        # 8. Agregar línea de producto
        line_id = odoo.add_product_line(
            sale_order_id,
            product_id=26174,
            qty=1,
            price=15950.00
        )
        # → line_id = 47587
```

**Paso 22: Obtener nombre de orden**
```python
        # 9. Leer nombre generado por Odoo
        sale_order = odoo.execute(
            'sale.order', 'read',
            [sale_order_id],
            ['name']
        )[0]
        # → name = "S15433"
```

**Paso 23: Completar tarea**
```python
        # 10. Resultado final
        result = {
            "partner_id": 124258,
            "partner_name": "Acme Corp",
            "lead_id": 27414,
            "opportunity_id": 27414,
            "sale_order_id": 18694,
            "sale_order_name": "S15433",
            "steps": {
                "partner": "Nuevo partner creado: Acme Corp (ID: 124258)",
                "lead": "Lead creado: Cotización Robot PUDU (ID: 27414)",
                "opportunity": "Convertido a oportunidad (ID: 27414)",
                "sale_order": "Cotización: S15433 (ID: 18694)",
                "product": "Producto 'MT1': $15950.0 (línea ID: 47587)"
            },
            "environment": "development"
        }
        
        # 11. Actualizar TaskManager
        task_manager.complete_task(tracking_id, result)
        # Estado: "completed", result guardado
```

**Paso 24-25: Logging y S3**
```python
        # 12. Actualizar log JSON
        quotation_logger.update_quotation_log(
            tracking_id,
            result,
            status="completed"
        )
        
        # 13. Upload a S3
        s3.upload_file(
            "/tmp/mcp_odoo_logs/2025-12-22_quot_abc123def456.log",
            "ilagentslogs",
            "mcp-odoo-logs/2025/12/quot_abc123def456.log"
        )
    
    except Exception as e:
        # Error handling
        task_manager.fail_task(tracking_id, str(e))
        quotation_logger.update_quotation_log(
            tracking_id, 
            {"error": str(e)},
            status="failed"
        )
```

**Paso 26: Thread termina**
```
Background thread completa su ejecución
Total elapsed: ~18-25 segundos
```

---

### **Fase 5: Consulta de Estado (Pasos 27-32) - OPCIONAL**

**Paso 27-28: Usuario pregunta estado**
```
Usuario: "¿Cuál es el estado de la cotización?"

LLM decide usar: dev_get_quotation_status(tracking_id="quot_abc123def456")
```

**Paso 29-31: Consulta vía MCP**
```json
POST /mcp/messages

{
  "method": "tools/call",
  "params": {
    "name": "dev_get_quotation_status",
    "arguments": {
      "tracking_id": "quot_abc123def456"
    }
  }
}
```

```python
# tools/crm.py

def dev_get_quotation_status(tracking_id: str):
    task = task_manager.get_task(tracking_id)
    return task.to_dict()
```

**Paso 32: Respuesta completa**
```json
{
  "tracking_id": "quot_abc123def456",
  "status": "completed",
  "created_at": "2025-12-22T15:30:00.123456",
  "elapsed_time": "18.5s",
  "progress": "Completado",
  "result": {
    "partner_id": 124258,
    "partner_name": "Acme Corp",
    "lead_id": 27414,
    "lead_name": "Cotización Robot PUDU",
    "opportunity_id": 27414,
    "sale_order_id": 18694,
    "sale_order_name": "S15433",
    "steps": { ... },
    "environment": "development"
  },
  "error": null,
  "completed_at": "2025-12-22T15:30:18.623456"
}
```

---

## ⏱️ Tiempos de Respuesta

| Fase | Tiempo | Descripción |
|------|--------|-------------|
| **Usuario → LLM** | ~500ms | LLM analiza y decide tool |
| **MCP Protocol** | ~50ms | JSON-RPC + routing |
| **Tool Init** | ~100ms | Genera tracking_id, crea task |
| **Respuesta al Usuario** | **~650ms** | ✅ Usuario recibe tracking_id |
| | | |
| **Background: Odoo Auth** | ~2s | XML-RPC authenticate |
| **Background: Partner** | ~3s | Buscar/crear partner |
| **Background: Lead** | ~3s | Crear lead |
| **Background: Opportunity** | ~2s | Convertir a opportunity |
| **Background: Sale Order** | ~4s | Crear orden de venta |
| **Background: Product Line** | ~3s | Agregar producto |
| **Background: Logging** | ~1s | Update log + S3 upload |
| **Total Background** | **~18-25s** | Usuario NO espera esto |

---

## 🔄 Flujo Alternativo: REST API (ElevenLabs)

Si la petición viene de **ElevenLabs** en lugar de Claude Desktop:

```
┌──────────┐  ┌──────────┐  ┌─────────┐
│ElevenLabs│  │ FastAPI  │  │  Tool   │
│ Webhook  │  │  Server  │  │ (crm.py)│
└────┬─────┘  └────┬─────┘  └────┬────┘
     │             │              │
     │  POST /api/quotation/async │
     │  (HTTP REST)               │
     ├────────────►│              │
     │             │  Valida JSON │
     │             │  (Pydantic)  │
     │             │              │
     │             │  Llama mismo código
     │             ├─────────────►│
     │             │   process_quotation_background()
     │             │              │
     │  202 Accepted              │
     │◄────────────┤              │
     │  {"tracking_id": "..."}    │
     │                            │
     │  [BACKGROUND = MISMO FLUJO PASOS 12-26]
     │                            │
     │  GET /api/quotation/status/{id}
     ├────────────►│              │
     │             │  task_manager.get_task()
     │             │              │
     │  200 OK                    │
     │◄────────────┤              │
     │  {"status": "completed"}   │
```

**CLAVE:** El código de procesamiento es **EXACTAMENTE EL MISMO** (`process_quotation_background()`), solo cambia el endpoint de entrada.

---

## 📊 Componentes Clave

### 1. **FastAPI Server (server.py)**
```python
# UN servidor, DOS protocolos:

app = FastAPI()  # ← Base HTTP

# Montar MCP
app.mount("/mcp", mcp.sse_app())

# Endpoints REST
@app.post("/api/quotation/async")
async def create_quotation_async(...):
    # Usa MISMO código que MCP
    pass
```

### 2. **TaskManager (core/task_manager.py)**
```python
# In-memory tracking (compartido por MCP y REST)

class TaskManager:
    def __init__(self):
        self._tasks: Dict[str, QuotationTask] = {}
    
    def create_task(self, tracking_id, params):
        task = QuotationTask(
            tracking_id=tracking_id,
            status="queued",
            created_at=datetime.now(),
            params=params
        )
        self._tasks[tracking_id] = task
    
    def get_task(self, tracking_id):
        return self._tasks.get(tracking_id)
```

### 3. **OdooClient (core/odoo_client.py)**
```python
# XML-RPC client para Odoo

class OdooClient:
    def authenticate(self):
        # Conecta y obtiene uid
        pass
    
    def get_or_create_partner(self, name, email, phone):
        # Busca por email, si no existe crea
        pass
    
    def create_lead(self, name, partner_id):
        # Crea oportunidad inicial
        pass
    
    def create_sale_order(self, partner_id):
        # Crea orden de venta
        pass
```

### 4. **QuotationLogger (core/logger.py)**
```python
# JSON logs + S3 upload

class QuotationLogger:
    def log_quotation(self, tracking_id, data):
        # Guarda log inicial en /tmp/
        pass
    
    def update_quotation_log(self, tracking_id, result):
        # Actualiza log con resultado
        # Upload a S3
        pass
```

---

## 🎯 Puntos Importantes

### ✅ **Respuesta Inmediata**
- Usuario recibe `tracking_id` en **~650ms**
- NO espera los 18-25 segundos de Odoo
- Puede continuar conversación mientras procesa

### ✅ **Estado Compartido**
- `TaskManager` es **in-memory** global
- Tanto MCP como REST acceden al mismo estado
- No necesita Redis/DB porque es un solo proceso

### ✅ **Código Reutilizado**
- `process_quotation_background()` es usado por:
  * `tools/crm.py::dev_create_quotation()` (MCP)
  * `server.py::create_quotation_async()` (REST)
- Sin duplicación de lógica

### ✅ **Logging Completo**
- Cada cotización genera log JSON en `/tmp/`
- Automáticamente sube a S3: `s3://ilagentslogs/mcp-odoo-logs/`
- Trazabilidad completa de cada operación

### ✅ **Error Handling**
- Si falla Odoo: Task status = "failed"
- Error guardado en TaskManager y log
- Usuario puede consultar error con `dev_get_quotation_status()`

---

## 🚀 Casos de Uso Reales

### **Caso 1: Claude Desktop (MCP)**
```
Usuario: "Haz una cotización para 2 robots PUDU, cliente Tech Corp"

Claude:
1. Analiza contexto
2. Llama dev_create_quotation() via MCP
3. Recibe tracking_id en 650ms
4. Responde: "Cotización iniciada! ID: quot_abc123. Te aviso cuando termine."
5. [18 segundos después]
6. Llama dev_get_quotation_status() automáticamente
7. Responde: "Cotización completada! Orden de venta: S15433"
```

### **Caso 2: ElevenLabs (REST)**
```
Usuario por voz: "Quiero cotizar un robot"

ElevenLabs Agent:
1. Recolecta datos por voz (nombre, email, teléfono)
2. POST /api/quotation/async
3. Recibe tracking_id
4. Responde por voz: "Estoy procesando tu cotización..."
5. [Polling cada 5 segundos]
6. GET /api/quotation/status/{tracking_id}
7. Cuando status="completed":
8. Responde por voz: "Tu cotización S15433 está lista!"
```

---

## 📝 Resumen Ejecutivo

**Flujo Completo en 3 Fases:**

1. **Síncrono (650ms):**
   - Usuario → LLM → MCP → FastAPI → Tool
   - Genera tracking_id
   - Respuesta inmediata

2. **Asíncrono (18-25s):**
   - Background thread
   - Procesa Odoo (Partner → Lead → Order → Product)
   - Actualiza TaskManager
   - Guarda logs → S3

3. **Consulta (Opcional):**
   - Usuario pregunta estado
   - Lee TaskManager
   - Retorna resultado completo

**Código Compartido = Arquitectura Eficiente** ✨
