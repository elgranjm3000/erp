#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "=========================================="
echo "TEST SISTEMA MULTI-MONEDA"
echo "=========================================="
echo ""

# 1. Listar monedas
echo "1. Monedas actuales:"
curl -s -X GET http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# 2. Crear VES
echo "2. Crear moneda VES:"
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"VES","name":"Bolívar","symbol":"Bs","exchange_rate":37.0,"is_base_currency":false}' | python3 -m json.tool
echo ""

# 3. Crear EUR
echo "3. Crear moneda EUR:"
curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"EUR","name":"Euro","symbol":"€","exchange_rate":0.92,"is_base_currency":false}' | python3 -m json.tool
echo ""

# 4. Crear categoría
echo "4. Crear categoría:"
curl -s -X POST http://localhost:8000/api/v1/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Electrónicos","description":"Productos electrónicos"}' | python3 -m json.tool
echo ""

# 5. Crear producto 1
echo "5. Crear Laptop:"
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Laptop HP","description":"Laptop 15.6","price":500,"quantity":10,"category_id":9}' | python3 -m json.tool
echo ""

# 6. Crear producto 2
echo "6. Crear Mouse:"
curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Mouse Logitech","description":"Mouse inalámbrico","price":20,"quantity":50,"category_id":9}' | python3 -m json.tool
echo ""

# 7. Crear cliente
echo "7. Crear cliente:"
curl -s -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Juan Pérez","email":"juan@test.com","phone":"0414-1234567","address":"Caracas"}' | python3 -m json.tool
echo ""

# 8. Crear almacén
echo "8. Crear almacén:"
curl -s -X POST http://localhost:8000/api/v1/warehouses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Almacén Principal","location":"Caracas"}' | python3 -m json.tool
echo ""

# 9. Crear factura MULTI-MONEDA
echo "=========================================="
echo "⭐ TEST PRINCIPAL: FACTURA MULTI-MONEDA"
echo "=========================================="
echo ""

echo "9. Crear factura con items en diferentes monedas:"
curl -s -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":13,"warehouse_id":13,"date":"2026-01-16","currency_id":1,"items":[{"product_id":14,"quantity":1,"currency_id":1},{"product_id":15,"quantity":2,"currency_id":2},{"product_id":16,"quantity":1,"currency_id":3}]}' | python3 -m json.tool
echo ""

echo "=========================================="
echo "✅ TEST COMPLETADO"
echo "=========================================="
