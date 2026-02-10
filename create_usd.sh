#!/bin/bash

curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}' > /tmp/login.json

TOKEN=$(python3 -c "import json; print(json.load(open('/tmp/login.json'))['access_token'])")

echo "Creando USD como moneda base..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"USD","name":"US Dollar","symbol":"$","exchange_rate":1.0,"is_base_currency":true}' | python3 -m json.tool
echo ""

echo "Listando monedas:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -c "import sys, json; data=json.load(sys.stdin); [print(f\"{c['code']} - ID: {c['id']}, Base: {c['is_base_currency']}, Rate: {c['exchange_rate']}\") for c in data]"
