#!/bin/bash

# Test completo de endpoints después del fix

BASE_URL="http://localhost:8000/api/v1"

echo "=== OBTENIENDO TOKEN ==="
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

echo "Token obtenido"
echo ""

# Usar moneda USD que debería existir
CURRENCY_ID=28

echo "=== 1. OBTENER HISTORIAL DE TASAS ==="
curl -s -X GET "$BASE_URL/currencies/$CURRENCY_ID/rate/history?limit=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== 2. OBTENER ESTADÍSTICAS ==="
curl -s -X GET "$BASE_URL/currencies/$CURRENCY_ID/statistics" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== 3. LISTAR CONFIG IGTF ==="
curl -s -X GET "$BASE_URL/currencies/igtf/config" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n=== 4. ACTUALIZAR TASA DE CAMBIO ==="
curl -s -X PUT "$BASE_URL/currencies/$CURRENCY_ID/rate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_rate": "38.5000000000",
    "change_reason": "Test del fix",
    "change_type": "manual",
    "change_source": "test_script"
  }' | python3 -m json.tool

echo -e "\n=== 5. VERIFICAR HISTORIAL DESPUÉS DE ACTUALIZAR ==="
curl -s -X GET "$BASE_URL/currencies/$CURRENCY_ID/rate/history?limit=2" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n✅ TODOS LOS TESTS COMPLETADOS"
