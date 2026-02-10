#!/bin/bash

# Test para reproducir error 422

BASE_URL="http://localhost:8000/api/v1"

echo "=== OBTENIENDO TOKEN ==="
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}')

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
  echo "ERROR: No se pudo obtener token"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "Token obtenido: ${TOKEN:0:20}..."
echo ""

echo "=== TEST 1: CREAR MONEDA SIN CAMPOS OPCIONALES ==="
RESPONSE1=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST1",
    "name": "Test Currency 1",
    "symbol": "T1",
    "exchange_rate": "10.50",
    "decimal_places": 2
  }')

echo "$RESPONSE1" | python3 -m json.tool
HTTP_CODE1=$(echo "$RESPONSE1" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('code', 200))" 2>/dev/null)
echo "HTTP Code: $HTTP_CODE1"
echo ""

echo "=== TEST 2: CREAR MONEDA CON TODOS LOS CAMPOS ==="
RESPONSE2=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "TEST2",
    "name": "Test Currency 2",
    "symbol": "T2",
    "exchange_rate": "20.7500000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": false,
    "igtf_rate": "3.00",
    "igtf_exempt": false,
    "rate_update_method": "manual"
  }')

echo "$RESPONSE2" | python3 -m json.tool
HTTP_CODE2=$(echo "$RESPONSE2" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('code', 200))" 2>/dev/null)
echo "HTTP Code: $HTTP_CODE2"
echo ""

echo "=== TEST 3: CREAR MONEDA VACÍA (DEBE FALLAR) ==="
RESPONSE3=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}')

echo "$RESPONSE3" | python3 -m json.tool
HTTP_CODE3=$(echo "$RESPONSE3" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('code', 200))" 2>/dev/null)
echo "HTTP Code: $HTTP_CODE3"
echo ""

echo "=== TEST 4: CREAR MONEDA DUPLICADA (DEBE FALLAR) ==="
RESPONSE4=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "USD",
    "name": "US Dollar Duplicate",
    "symbol": "$",
    "exchange_rate": "999.99"
  }')

echo "$RESPONSE4" | python3 -m json.tool
HTTP_CODE4=$(echo "$RESPONSE4" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('code', 200))" 2>/dev/null)
echo "HTTP Code: $HTTP_CODE4"
