#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbiIsImNvbXBhbnlfaWQiOjgsInJvbGUiOiJhZG1pbiIsImlzX2NvbXBhbnlfYWRtaW4iOnRydWUsImV4cCI6MTc2ODQ3NTg2MH0.M_0vD4u5j4HNgsotBXathNBf4T0gOlcH0yMKsYeLNkE"

echo "========================================="
echo "⭐ TEST SISTEMA MULTI-MONEDA"
echo "========================================="
echo ""

echo "1. Verificando monedas:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); print(json.dumps(data, indent=2))"
echo ""

echo "2. Creando VES..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"VES","name":"Bolivar","symbol":"Bs","exchange_rate":37.0,"is_base_currency":false}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

echo "3. Creando EUR..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"EUR","name":"Euro","symbol":"€","exchange_rate":0.92,"is_base_currency":false}' | python3 -c "import sys, json; print(json.dumps(json.load(sys.stdin), indent=2))"
echo ""

echo "4. Monedas finales:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"{c['code']} - ID: {c['id']}, Base: {c['is_base_currency']}, Rate: {c['exchange_rate']}\") for c in data]"
echo ""

echo "========================================="
echo "Ahora creamos factura multi-moneda..."
echo "========================================="
