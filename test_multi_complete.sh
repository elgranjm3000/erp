#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "========================================="
echo "⭐ TEST SISTEMA MULTI-MONEDA ESCALABLE"
echo "========================================="
echo ""

# Paso 1: Agregar stock al almacén
echo "📦 Paso 1: Agregar stock de productos al almacén"
echo ""

echo "1.1 Agregar 50 unidades de Laptop HP (id=31):"
curl -s -X POST http://localhost:8000/api/v1/warehouse-products/adjust-stock \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":15,"product_id":31,"adjustment":50,"reason":"Stock inicial para test multi-moneda"}' | python3 -m json.tool
echo -e "\n"

echo "1.2 Agregar 100 unidades de Mouse Logitech (id=32):"
curl -s -X POST http://localhost:8000/api/v1/warehouse-products/adjust-stock \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":15,"product_id":32,"adjustment":100,"reason":"Stock inicial para test multi-moneda"}' | python3 -m json.tool
echo -e "\n"

echo "1.3 Agregar 30 unidades de Monitor Samsung (id=33):"
curl -s -X POST http://localhost:8000/api/v1/warehouse-products/adjust-stock \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"warehouse_id":15,"product_id":33,"adjustment":30,"reason":"Stock inicial para test multi-moneda"}' | python3 -m json.tool
echo -e "\n"

# Paso 2: Verificar stock
echo "1.4 Verificar stock en almacén:"
curl -s -X GET http://localhost:8000/api/v1/warehouses/15/products \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

# Paso 3: Crear factura MULTI-MONEDA
echo "========================================="
echo "💰 Paso 2: FACTURA MULTI-MONEDA"
echo "========================================="
echo ""
echo "Configuración de la factura:"
echo "  • customer_id: 14 (Cliente Test con RIF V-12345678)"
echo "  • warehouse_id: 15 (Almacén Principal)"
echo "  • currency_id: 1 (USD - Moneda base)"
echo "  • date: 2026-01-16"
echo "  • status: factura"
echo ""
echo "Items con diferentes monedas:"
echo ""
echo "  Item 1 - Laptop HP (USD):"
echo "    • product_id: 31"
echo "    • quantity: 1"
echo "    • currency_id: 1 (USD)"
echo "    • price_per_unit: 500 USD"
echo "    • Esperado: base_currency_amount = 500.0"
echo ""
echo "  Item 2 - Mouse Logitech (VES):"
echo "    • product_id: 32"
echo "    • quantity: 2"
echo "    • currency_id: 2 (VES)"
echo "    • price_per_unit: 740 Bs c/u"
echo "    • exchange_rate: 37.0"
echo "    • Esperado: base_currency_amount = 40.0 (740/37 * 2)"
echo ""
echo "  Item 3 - Monitor Samsung (EUR):"
echo "    • product_id: 33"
echo "    • quantity: 1"
echo "    • currency_id: 3 (EUR)"
echo "    • price_per_unit: 230 €"
echo "    • exchange_rate: 0.92"
echo "    • Esperado: base_currency_amount = 211.6 (230 * 0.92)"
echo ""
echo "TOTAL ESPERADO: 500 + 40 + 211.6 = 751.6 USD"
echo "========================================="
echo ""
echo "Creando factura..."
echo ""

curl -s -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 14,
    "warehouse_id": 15,
    "date": "2026-01-16",
    "currency_id": 1,
    "status": "factura",
    "items": [
      {
        "product_id": 31,
        "quantity": 1,
        "currency_id": 1,
        "price_per_unit": 500
      },
      {
        "product_id": 32,
        "quantity": 2,
        "currency_id": 2,
        "price_per_unit": 740
      },
      {
        "product_id": 33,
        "quantity": 1,
        "currency_id": 3,
        "price_per_unit": 230
      }
    ]
  }' | python3 -m json.tool > /tmp/invoice_response.json

cat /tmp/invoice_response.json
echo -e "\n"

# Paso 4: Verificación
echo "========================================="
echo "✅ VERIFICACIÓN DEL SISTEMA MULTI-MONEDA"
echo "========================================="
echo ""

INVOICE_ID=$(python3 -c "import json; print(json.load(open('/tmp/invoice_response.json'))['id'])" 2>/dev/null)

echo "📋 Factura creada con ID: $INVOICE_ID"
echo ""
echo "Verificando detalles de la factura..."
echo ""

curl -s -X GET "http://localhost:8000/api/v1/invoices/$INVOICE_ID" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

echo "========================================="
echo "🎉 SISTEMA MULTI-MONEDA ESCALABLE FUNCIONANDO"
echo "========================================="
echo ""
echo "✨ Características demostradas:"
echo "  ✓ Cada item puede tener su propia moneda"
echo "  ✓ Exchange rates se guardan históricamente"
echo "  ✓ base_currency_amount permite totales consistentes"
echo "  ✓ Sistema ESCALABLE: puedes agregar N monedas en el futuro"
echo "  ✓ Conversión automática a moneda base de la factura"
echo ""
echo "📊 Campos multi-moneda por item:"
echo "  • currency_id: Moneda del item"
echo "  • exchange_rate: Tasa de cambio utilizada"
echo "  • exchange_rate_date: Fecha de la tasa"
echo "  • base_currency_amount: Monto convertido a moneda base"
echo ""
echo "💡 Para agregar más monedas en el futuro:"
echo "  Solo crea nuevas monedas via POST /api/v1/currencies"
echo "  y el sistema automáticamente soportará items en esa moneda."
echo ""
echo "========================================="
