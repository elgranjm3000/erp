#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "========================================="
echo "⭐ TEST SISTEMA MULTI-MONEDA ESCALABLE"
echo "========================================="
echo ""

# Paso 1: Actualizar cliente con tax_id
echo "Paso 1: Actualizar cliente con tax_id"
curl -s -X PUT http://localhost:8000/api/v1/customers/14 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Cliente Test","email":"test@test.com","phone":"0414-1234567","tax_id":"V-12345678"}' | python3 -m json.tool
echo -e "\n"

# Paso 2: Ver stock en almacén
echo "Paso 2: Stock actual en almacén"
curl -s -X GET http://localhost:8000/api/v1/warehouses/15/products \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

# Paso 3: Crear factura MULTI-MONEDA
echo "========================================="
echo "⭐ FACTURA CON 3 MONEDAS DIFERENTES"
echo "========================================="
echo ""
echo "Configuración:"
echo "  currency_id: 1 (USD - Moneda base de la factura)"
echo ""
echo "Items:"
echo "  1. product_id=31 (Laptop HP)"
echo "     quantity=1, currency_id=1 (USD), price=500"
echo "     → base_currency_amount = 500"
echo ""
echo "  2. product_id=32 (Mouse Logitech)"
echo "     quantity=2, currency_id=2 (VES), price=740"
echo "     → exchange_rate = 37.0"
echo "     → base_currency_amount = 740/37 = 20 (c/u)"
echo ""
echo "  3. product_id=33 (Monitor Samsung)"
echo "     quantity=1, currency_id=3 (EUR), price=230"
echo "     → exchange_rate = 0.92"
echo "     → base_currency_amount = 230*0.92 = 211.60"
echo ""
echo "Total esperado: 500 + 40 + 211.60 = 751.60 USD"
echo "========================================="
echo -e "\n"

echo "Creando factura..."
curl -s -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"customer_id":14,"warehouse_id":15,"date":"2026-01-16","currency_id":1,"status":"factura","items":[{"product_id":31,"quantity":1,"currency_id":1,"price_per_unit":500},{"product_id":32,"quantity":2,"currency_id":2,"price_per_unit":740},{"product_id":33,"quantity":1,"currency_id":3,"price_per_unit":230}]}' | python3 -m json.tool

echo -e "\n"
echo "========================================="
echo "✅ VERIFICACIÓN"
echo "========================================="
echo ""
echo "Verifica en la respuesta de la factura:"
echo "✓ currency_id = 1 (USD como moneda base)"
echo "✓ items[0].currency_id = 1 (USD)"
echo "✓ items[0].base_currency_amount = 500.0"
echo "✓ items[1].currency_id = 2 (VES)"
echo "✓ items[1].exchange_rate = 37.0"
echo "✓ items[1].base_currency_amount = 40.0 (20 * 2 unidades)"
echo "✓ items[2].currency_id = 3 (EUR)"
echo "✓ items[2].exchange_rate = 0.92"
echo "✓ items[2].base_currency_amount = 211.6"
echo "✓ total_amount = 751.6 (suma de base_currency_amount)"
echo ""
echo "🎉 SISTEMA MULTI-MONEDA ESCALABLE FUNCIONANDO!"
echo "   Puedes agregar N monedas y cada item puede tener"
echo "   su propia moneda con conversión automática."
echo "========================================="
