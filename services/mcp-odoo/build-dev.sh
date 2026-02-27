#!/usr/bin/env bash
set -euo pipefail

echo "════════════════════════════════════════════════════════════════════"
echo "🔧 BUILD Y PUSH DE IMAGEN :dev (App Runner NO afectado)"
echo "════════════════════════════════════════════════════════════════════"
echo ""

AWS_REGION=${AWS_REGION:-us-east-1}

echo "📦 1. Building imagen local con tag :dev..."
docker build -t mcp-odoo:dev .
echo "✅ Imagen local creada: mcp-odoo:dev"
echo ""

echo "🔍 2. Obteniendo cuenta AWS..."
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
echo "✅ Cuenta: $ACCOUNT_ID"
echo "✅ ECR: $ECR"
echo ""

echo "🔐 3. Login a ECR..."
aws ecr get-login-password --region "$AWS_REGION" \
| docker login --username AWS --password-stdin "$ECR"
echo "✅ Autenticado en ECR"
echo ""

echo "📝 4. Verificando repositorio ECR..."
aws ecr describe-repositories --repository-names mcp-odoo --region "$AWS_REGION" >/dev/null 2>&1 \
|| aws ecr create-repository --repository-name mcp-odoo --region "$AWS_REGION" >/dev/null
echo "✅ Repositorio mcp-odoo existe"
echo ""

echo "🏷️  5. Tagging imagen para ECR con :dev..."
docker tag mcp-odoo:dev "$ECR/mcp-odoo:dev"
echo "✅ Tag aplicado: $ECR/mcp-odoo:dev"
echo ""

echo "🚀 6. Pushing imagen :dev a ECR..."
docker push "$ECR/mcp-odoo:dev"
echo ""

echo "════════════════════════════════════════════════════════════════════"
echo "✅ COMPLETADO EXITOSAMENTE"
echo "════════════════════════════════════════════════════════════════════"
echo ""
echo "📍 Imagen subida: $ECR/mcp-odoo:dev"
echo ""
echo "⚠️  IMPORTANTE:"
echo "   • App Runner NO fue afectado (sigue usando :latest)"
echo "   • La imagen :latest NO fue modificada"
echo "   • Esta es una imagen separada para desarrollo/pruebas"
echo ""
echo "� Variables de entorno requeridas en App Runner:"
echo "   • ODOO_ENVIRONMENT=dev"
echo "   • ODOO_URL, ODOO_DB, ODOO_LOGIN, ODOO_API_KEY (PRODUCCIÓN)"
echo "   • DEV_ODOO_URL, DEV_ODOO_DB, DEV_ODOO_LOGIN, DEV_ODOO_API_KEY"
echo "   • AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY"
echo "   • S3_BUCKET_NAME=ilagentslogs"
echo "   • S3_REGION=us-west-2"
echo "   • TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN"
echo "   • TWILIO_FROM_NUMBER, VENDEDOR_WHATSAPP"
echo "   • LAMBDA_ODOO_SUPERVISOR_URL, LAMBDA_EMAIL_SENDER_URL"
echo "   • MESSAGE_CHANNEL=whatsapp"
echo "   • ENABLE_ERROR_NOTIFICATIONS=true"
echo ""
echo "🔧 Configuración del código:"
echo "   • BOT IDs por ambiente:"
echo "     - DEV: OdooBot (106917), Lexi Aria (109061)"
echo "     - PROD: OdooBot (2), Lexi Aria (109061)"
echo "   • Puerto: 8000"
echo "   • Health check: /health"
echo ""
echo "💡 Para usar esta imagen en App Runner:"
echo "   1. Ir a AWS App Runner → Servicios"
echo "   2. Seleccionar servicio o crear nuevo"
echo "   3. Configurar imagen: $ECR/mcp-odoo:dev"
echo "   4. Configurar todas las variables de entorno listadas arriba"
echo "   5. Deploy automático iniciará"
echo ""
echo "════════════════════════════════════════════════════════════════════"
