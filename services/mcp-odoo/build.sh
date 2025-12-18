#!/usr/bin/env bash
set -euo pipefail

AWS_REGION=${AWS_REGION:-us-east-1}

docker build -t mcp-odoo:latest .

ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR="$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# ⬇️ LOGIN A ECR (renueva token que expira)
aws ecr get-login-password --region "$AWS_REGION" \
| docker login --username AWS --password-stdin "$ECR"

# (opcional) crea el repo si no existe
aws ecr describe-repositories --repository-names mcp-odoo --region "$AWS_REGION" >/dev/null 2>&1 \
|| aws ecr create-repository --repository-name mcp-odoo --region "$AWS_REGION" >/dev/null

docker tag mcp-odoo:latest "$ECR/mcp-odoo:latest"
docker push "$ECR/mcp-odoo:latest"
echo "OK → $ECR/mcp-odoo:latest"