#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "========================================="
echo "Configurando monedas para test"
echo "========================================="
echo ""

echo "1. Creando USD como moneda base..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"USD","name":"US Dollar","symbol":"$","exchange_rate":1.0,"is_base_currency":true}' | python3 -m json.tool
echo -e "\n"

echo "2. Creando VES..."
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"VES","name":"Bolivar","symbol":"Bs","exchange_rate":37.0,"is_base_currency":false}' | python3 -m json.tool
echo -e "\n"

echo "3. Verificando monedas configuradas:"
curl -s http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""
