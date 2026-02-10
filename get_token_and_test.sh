#!/bin/bash

echo "Obteniendo nuevo token..."
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' > /tmp/login_response.json

TOKEN=$(python3 -c "import json; print(json.load(open('/tmp/login_response.json'))['access_token'])")

echo "Token obtenido!"
echo ""

echo "Verificando monedas actuales:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

echo "Creando VES..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"VES","name":"Bolivar","symbol":"Bs","exchange_rate":37.0,"is_base_currency":false}' | python3 -m json.tool
echo ""

echo "Creando EUR..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"EUR","name":"Euro","symbol":"€","exchange_rate":0.92,"is_base_currency":false}' | python3 -m json.tool
echo ""

echo "Monedas configuradas:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"{c['code']} - ID: {c['id']}, Base: {c['is_base_currency']}\") for c in data]"
echo ""

echo "========================================="
echo "⭐ AHORA CREAR FACTURA MULTI-MONEDA"
echo "========================================="
