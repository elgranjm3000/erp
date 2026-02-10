#!/bin/bash

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0bXVsdGkiLCJjb21wYW55X2lkIjo5LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njg0NzMyNjF9.hUkgFOF4-2wwmAvwouKnm3ehgUdaQayuBbTpjsu3VOs"

echo "========================================="
echo "TEST SISTEMA MULTI-MONEDA ESCALABLE"
echo "========================================="
echo ""

# Test 1: Listar monedas existentes
echo "1. Listar monedas existentes:"
curl -s -X GET http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

# Test 2: Crear monedas
echo "2. Crear moneda VES:"
VES_ID=$(curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VES",
    "name": "Bolívar",
    "symbol": "Bs",
    "exchange_rate": 37.0,
    "is_base_currency": false
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   VES ID: $VES_ID"

echo -e "\n3. Crear moneda EUR:"
EUR_ID=$(curl -s -X POST http://localhost:8000/api/v1/currencies \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "EUR",
    "name": "Euro",
    "symbol": "€",
    "exchange_rate": 0.92,
    "is_base_currency": false
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   EUR ID: $EUR_ID"
echo -e "\n"

# Test 3: Crear categoría
echo "4. Crear categoría:"
CATEGORY_ID=$(curl -s -X POST http://localhost:8000/api/v1/categories \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Electrónicos"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Categoría ID: $CATEGORY_ID"
echo -e "\n"

# Test 4: Crear productos
echo "5. Crear Laptop:"
PRODUCT_1=$(curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Laptop HP",
    "description": "Laptop HP 15.6\"",
    "price": 500,
    "quantity": 10,
    "category_id": '"$CATEGORY_ID"'
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Laptop ID: $PRODUCT_1"

echo -e "\n6. Crear Mouse:"
PRODUCT_2=$(curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Mouse Logitech",
    "description": "Mouse inalámbrico",
    "price": 20,
    "quantity": 50,
    "category_id": '"$CATEGORY_ID"'
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Mouse ID: $PRODUCT_2"

echo -e "\n7. Crear Monitor:"
PRODUCT_3=$(curl -s -X POST http://localhost:8000/api/v1/products \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monitor Samsung",
    "description": "Monitor 24 pulgadas",
    "price": 250,
    "quantity": 20,
    "category_id": '"$CATEGORY_ID"'
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Monitor ID: $PRODUCT_3"
echo -e "\n"

# Test 5: Sincronizar precios a todas las monedas
echo "8. Sincronizar precios del Laptop a todas las monedas:"
curl -s -X POST http://localhost:8000/api/v1/products/$PRODUCT_1/prices/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_price": 500,
    "base_currency_id": 1
  }' | python3 -m json.tool
echo -e "\n"

echo "9. Sincronizar precios del Mouse:"
curl -s -X POST http://localhost:8000/api/v1/products/$PRODUCT_2/prices/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_price": 20,
    "base_currency_id": 1
  }' | python3 -m json.tool
echo -e "\n"

echo "10. Sincronizar precios del Monitor:"
curl -s -X POST http://localhost:8000/api/v1/products/$PRODUCT_3/prices/sync \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "base_price": 250,
    "base_currency_id": 1
  }' | python3 -m json.tool
echo -e "\n"

# Test 6: Ver precios de un producto
echo "11. Ver todos los precios del Laptop:"
curl -s -X GET http://localhost:8000/api/v1/products/$PRODUCT_1/prices \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo -e "\n"

# Test 7: Registrar tasas de cambio
echo "12. Registrar tasa de cambio USD->VES:"
curl -s -X POST http://localhost:8000/api/v1/currencies/exchange-rates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_currency_id": 1,
    "to_currency_id": '"$VES_ID"',
    "rate": 37.0,
    "recorded_at": "2026-01-16T09:00:00"
  }' | python3 -m json.tool
echo -e "\n"

echo "13. Registrar tasa de cambio USD->EUR:"
curl -s -X POST http://localhost:8000/api/v1/currencies/exchange-rates \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "from_currency_id": 1,
    "to_currency_id": '"$EUR_ID"',
    "rate": 0.92,
    "recorded_at": "2026-01-16T09:00:00"
  }' | python3 -m json.tool
echo -e "\n"

# Test 8: Crear cliente y almacén
echo "14. Crear cliente:"
CUSTOMER_ID=$(curl -s -X POST http://localhost:8000/api/v1/customers \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Juan Pérez",
    "email": "juan@test.com",
    "phone": "0414-1234567",
    "address": "Caracas"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Cliente ID: $CUSTOMER_ID"

echo -e "\n15. Crear almacén:"
WAREHOUSE_ID=$(curl -s -X POST http://localhost:8000/api/v1/warehouses \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Almacén Principal",
    "location": "Caracas"
  }' | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

echo "   Almacén ID: $WAREHOUSE_ID"
echo -e "\n"

# Test 9: CREAR FACTURA MULTI-MONEDA
echo "========================================="
echo "⭐ TEST PRINCIPAL: FACTURA MULTI-MONEDA"
echo "========================================="
echo ""

echo "16. Crear factura con items en 3 monedas diferentes:"
echo "    - Item 1: Laptop en USD"
echo "    - Item 2: Mouse en VES"
echo "    - Item 3: Monitor en EUR"
echo ""

curl -s -X POST http://localhost:8000/api/v1/invoices/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": '$CUSTOMER_ID',
    "warehouse_id": '$WAREHOUSE_ID',
    "date": "2026-01-16",
    "currency_id": 1,
    "items": [
      {
        "product_id": '$PRODUCT_1',
        "quantity": 1,
        "currency_id": 1
      },
      {
        "product_id": '$PRODUCT_2',
        "quantity": 2,
        "currency_id": '$VES_ID'
      },
      {
        "product_id": '$PRODUCT_3',
        "quantity": 1,
        "currency_id": '$EUR_ID'
      }
    ]
  }' | python3 -m json.tool

echo ""
echo "========================================="
echo "✅ TEST COMPLETADO"
echo "========================================="
echo ""
echo "Verifica que:"
echo "1. La factura se creó con currency_id=1 (USD)"
echo "2. Item 1 tiene currency_id=1 (USD), base_currency_amount=500"
echo "3. Item 2 tiene currency_id=2 (VES), exchange_rate=37.0, base_currency_amount≈40.54"
echo "4. Item 3 tiene currency_id=3 (EUR), exchange_rate=0.92, base_currency_amount≈230"
echo "5. total_amount es la suma de todos los base_currency_amount"
