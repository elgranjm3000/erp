#!/bin/bash

# Test del fix de monedas

BASE_URL="http://localhost:8000/api/v1"

echo "=== OBTENIENDO TOKEN ==="
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "Token obtenido: ${TOKEN:0:20}..."
echo ""

echo "=== CREANDO MONEDA CAD (Canadian Dollar) ==="
RESPONSE=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "CAD",
    "name": "Canadian Dollar",
    "symbol": "C$",
    "exchange_rate": "27.1500000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": false,
    "rate_update_method": "manual"
  }')

echo "$RESPONSE" | python3 -m json.tool

# Verificar si hay error
ERROR=$(echo "$RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print('error' in data)" 2>/dev/null)

if [ "$ERROR" == "True" ]; then
  echo -e "\n❌ ERROR: La moneda NO se creó correctamente"
  exit 1
else
  echo -e "\n✅ EXITO: Moneda creada correctamente"
fi
