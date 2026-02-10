#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "========================================="
echo "TEST SISTEMA MULTI-MONEDA ESCALABLE"
echo "========================================="
echo ""

# 1. Ver monedas actuales
echo "1. Monedas disponibles:"
curl -s -X GET http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

# 2. Crear moneda VES
echo "2. Crear moneda VES:"
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"VES","name":"Bolivar","symbol":"Bs","exchange_rate":37.0,"is_base_currency":false}' | python3 -m json.tool
echo -e "\n"

# 3. Crear productos para test
echo "3. Crear producto Laptop:"
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop HP Test","description":"Test product","price":500,"quantity":100}' | python3 -m json.tool
echo -e "\n"

echo "4. Crear producto Mouse:"
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse Test","description":"Test mouse","price":20,"quantity":100}' | python3 -m json.tool
echo -e "\n"

# 4. Crear cliente
echo "5. Crear cliente:"
curl -s -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Cliente Test","email":"test@test.com","phone":"0414-1234567"}' | python3 -m json.tool
echo -e "\n"

# 5. Crear factura MULTI-MONEDA
echo "========================================="
echo "⭐ TEST PRINCIPAL: FACTURA MULTI-MONEDA"
echo "========================================="
echo "6. Crear factura con items en diferentes monedas:"
echo "   - Laptop en USD (currency_id=1)"
echo "   - Mouse en VES (currency_id=2)"
echo ""

curl -s -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":14,"date":"2026-01-16","currency_id":1,"status":"presupuesto","items":[{"product_id":31,"quantity":1,"currency_id":1,"price_per_unit":500},{"product_id":32,"quantity":2,"currency_id":2,"price_per_unit":740}]}' | python3 -m json.tool

echo -e "\n"
echo "========================================="
echo "✅ TEST COMPLETADO"
echo "========================================="
echo ""
echo "Verifica en la respuesta:"
echo "1. currency_id=1 (USD como moneda base de la factura)"
echo "2. Item 1: currency_id=1 (USD), base_currency_amount=500"
echo "3. Item 2: currency_id=2 (VES), exchange_rate≈37.0, base_currency_amount≈20 (740/37)"
echo "4. total_amount debe ser ≈520 USD (500 + 20)"
