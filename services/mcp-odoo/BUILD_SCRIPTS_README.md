# 🚀 Scripts de Build y Deploy

## 📋 Resumen

Este directorio contiene **DOS scripts de build** para diferentes propósitos:

| Script | Tag | Afecta App Runner | Propósito |
|--------|-----|-------------------|-----------|
| `build.sh` | `:latest` | ✅ **SÍ** | Deploy a producción |
| `build-dev.sh` | `:dev` | ❌ **NO** | Desarrollo/pruebas |

---

## 🔧 `build.sh` - Deploy a Producción

### ⚠️ CUIDADO: Este script afecta App Runner

```bash
./build.sh
```

**Lo que hace:**
1. Build de imagen con tag `:latest`
2. Push a ECR: `{ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/mcp-odoo:latest`
3. App Runner detecta cambios y puede auto-deployar

**Cuándo usar:**
- ✅ Cuando quieres desplegar a producción
- ✅ Cuando has probado cambios en dev
- ✅ Cuando estás listo para actualizar el servicio en vivo

**Precauciones:**
- ⚠️ Verifica que tus cambios estén probados
- ⚠️ App Runner puede tardar ~5-10 min en actualizar
- ⚠️ Considera hacer backup de configuración

---

## 🧪 `build-dev.sh` - Desarrollo/Pruebas

### ✅ SEGURO: NO afecta App Runner

```bash
./build-dev.sh
```

**Lo que hace:**
1. Build de imagen con tag `:dev`
2. Push a ECR: `{ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/mcp-odoo:dev`
3. App Runner NO es afectado (sigue usando `:latest`)

**Cuándo usar:**
- ✅ Para subir cambios de desarrollo
- ✅ Para compartir con equipo sin afectar producción
- ✅ Para testing en ambientes separados
- ✅ Cuando te piden "sube una imagen con tag :dev"

**Ventajas:**
- ✅ 100% seguro para producción
- ✅ Permite múltiples versiones en ECR
- ✅ Fácil rollback si algo falla

---

## 📊 Flujo de Trabajo Recomendado

### Opción 1: Desarrollo Normal
```bash
# 1. Hacer cambios en código
vim core/quotation_service.py

# 2. Subir a :dev para pruebas
./build-dev.sh

# 3. Probar en ambiente dev
docker run -p 8000:8000 {ECR}/mcp-odoo:dev

# 4. Si funciona, deploy a producción
./build.sh
```

### Opción 2: Solo Development (SEGURO)
```bash
# Solo subir a :dev (producción intacta)
./build-dev.sh
```

### Opción 3: Deploy Directo a Producción (CUIDADO)
```bash
# Deploy directo (solo si estás seguro)
./build.sh
```

---

## 🔍 Verificar Imágenes en ECR

```bash
# Listar todas las imágenes
aws ecr describe-images \
  --repository-name mcp-odoo \
  --region us-east-1

# Ver solo tags
aws ecr list-images \
  --repository-name mcp-odoo \
  --region us-east-1 \
  --query 'imageIds[*].imageTag'
```

**Salida esperada:**
```json
[
  "latest",  // ← App Runner usa este
  "dev"      // ← Tu imagen de desarrollo
]
```

---

## 🎯 Configuración de App Runner

App Runner está configurado para usar **SOLO** el tag `:latest`:

```
Source: {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/mcp-odoo:latest
                                                                ^^^^^^
                                                        Tag específico
```

**Esto significa:**
- ✅ Puedes subir `:dev`, `:staging`, `:v1.0.0`, etc. sin afectar producción
- ✅ Solo cuando subes `:latest` se actualiza App Runner
- ✅ Puedes tener múltiples versiones en ECR simultáneamente

---

## 🛡️ Garantías de Seguridad

### ❌ Lo que NO va a pasar con `build-dev.sh`:
- ❌ App Runner NO se va a actualizar
- ❌ La imagen `:latest` NO se va a sobrescribir
- ❌ Producción NO se va a afectar
- ❌ Los usuarios NO van a ver cambios

### ✅ Lo que SÍ va a pasar con `build-dev.sh`:
- ✅ Nueva imagen `:dev` en ECR
- ✅ Disponible para pull/testing
- ✅ Producción intacta y funcionando
- ✅ Puedes probar en otro ambiente

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Te piden subir imagen :dev
```bash
cd /home/devsoft/Documentos/Daniel_Agent_Project/services/mcp-odoo
./build-dev.sh
# ✅ Listo, imagen :dev subida, producción intacta
```

### Ejemplo 2: Deploy a producción
```bash
cd /home/devsoft/Documentos/Daniel_Agent_Project/services/mcp-odoo
./build.sh
# ⚠️ App Runner se actualizará en ~5-10 minutos
```

### Ejemplo 3: Testing local con imagen :dev
```bash
# Descargar imagen :dev de ECR
docker pull {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/mcp-odoo:dev

# Correr localmente
docker run -p 8000:8000 --env-file .env {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/mcp-odoo:dev
```

---

## 🔐 Variables de Ambiente

Ambos scripts usan:
```bash
AWS_REGION=${AWS_REGION:-us-east-1}
```

Para cambiar región:
```bash
AWS_REGION=us-west-2 ./build-dev.sh
```

---

## 🆘 Troubleshooting

### Problema: "denied: Your authorization token has expired"
```bash
# Re-autenticar
aws ecr get-login-password --region us-east-1 \
| docker login --username AWS --password-stdin {ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com
```

### Problema: "repository does not exist"
```bash
# Crear repositorio
aws ecr create-repository --repository-name mcp-odoo --region us-east-1
```

### Problema: "No space left on device"
```bash
# Limpiar imágenes viejas
docker system prune -a
```

---

## 📞 Contacto

Para dudas sobre estos scripts:
- Revisar este README
- Consultar logs del script
- Verificar configuración de App Runner en AWS Console

---

**Última actualización**: 2026-02-25
