#!/bin/bash

# Test de API - Sistema de Monedas Venezolano
# Prueba endpoints de configuración de monedas

echo "🇻🇪==============================================🇻🇪"
echo "  TEST API - SISTEMA DE MONEDAS VENEZOLANO"
echo "🇻🇪==============================================🇻🇪"
echo ""

# Token de autenticación (necesitas cambiarlo por uno válido)
# Genera un token con: python3 -c "from auth import create_access_token; print(create_access_token(...))"

TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0dXNlcjIiLCJjb21wYW55X2lkIjo1LCJyb2xlIjoiYWRtaW4iLCJpc19jb21wYW55X2FkbWluIjp0cnVlLCJleHAiOjE3Njc3NDAyNzJ9.vfIIxGeTPYBG25tOY4zFWxd2vrqu9PWLNIm-eP9TcNA"

API_URL="http://localhost:8000/api/v1"

echo ""
echo "=========================================="
echo "1. LISTAR MONEDAS"
echo "=========================================="
curl -s -X GET "$API_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "\n=========================================="
echo "2. CREAR MONEDA VES (BASE)"
echo "=========================================="
VES_RESPONSE=$(curl -s -X POST "$API_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VES",
    "name": "Bolívar Soberano",
    "symbol": "Bs",
    "exchange_rate": "1.0000000000",
    "decimal_places": 2,
    "is_base_currency": true,
    "conversion_method": null,
    "applies_igtf": false,
    "igtf_exempt": true,
    "rate_update_method": "manual"
  }')

echo "$VES_RESPONSE" | python3 -m json.tool

VES_ID=$(echo "$VES_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "VES ID: $VES_ID"

echo ""
echo "\n=========================================="
echo "3. CREAR MONEDA USD (CON IGTF)"
echo "=========================================="
USD_RESPONSE=$(curl -s -X POST "$API_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "USD",
    "name": "US Dollar",
    "symbol": "$",
    "exchange_rate": "36.5000000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": true,
    "igtf_rate": "3.00",
    "igtf_min_amount": "1000.00",
    "rate_update_method": "api_bcv",
    "rate_source_url": "https://www.bcv.org.ve"
  }')

echo "$USD_RESPONSE" | python3 -m json.tool

USD_ID=$(echo "$USD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "USD ID: $USD_ID"

echo ""
echo "\n=========================================="
echo "4. CREAR MONEDA EUR (CON IGTF)"
echo "=========================================="
EUR_RESPONSE=$(curl -s -X POST "$API_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "EUR",
    "name": "Euro",
    "symbol": "€",
    "exchange_rate": "39.8000000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": true,
    "igtf_rate": "3.00",
    "rate_update_method": "api_fixer",
    "rate_source_url": "https://api.fixer.io/latest"
  }')

echo "$EUR_RESPONSE" | python3 -m json.tool

EUR_ID=$(echo "$EUR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', ''))" 2>/dev/null)
echo "EUR ID: $EUR_ID"

echo ""
echo "\n=========================================="
echo "5. OBTENER MONEDA USD"
echo "=========================================="
if [ ! -z "$USD_ID" ]; then
  curl -s -X GET "$API_URL/currencies/$USD_ID" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""
echo "\n=========================================="
echo "6. ACTUALIZAR TASA DE USD (CON HISTORIAL)"
echo "=========================================="
if [ ! -z "$USD_ID" ]; then
  curl -s -X PUT "$API_URL/currencies/$USD_ID/rate" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "new_rate": "37.5000000000",
      "change_reason": "Actualización diaria BCV - Tasa oficial",
      "change_type": "automatic_api",
      "change_source": "api_bcv",
      "provider_metadata": {
        "api_response_time": "150ms",
        "bcv_timestamp": "2026-01-15T10:00:00"
      }
    }' | python3 -m json.tool
fi

echo ""
echo "\n=========================================="
echo "7. VER HISTORIAL DE TASA USD"
echo "=========================================="
if [ ! -z "$USD_ID" ]; then
  curl -s -X GET "$API_URL/currencies/$USD_ID/rate/history?limit=5" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""
echo "\n=========================================="
echo "8. CONVERTIR USD A VES"
echo "=========================================="
curl -s -X GET "$API_URL/currencies/convert?from_currency=USD&to_currency=VES&amount=100" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "\n=========================================="
echo "9. CALCULAR IGTF PARA USD"
echo "=========================================="
if [ ! -z "$USD_ID" ]; then
  curl -s -X POST "$API_URL/currencies/igtf/calculate?amount=1500&currency_id=$USD_ID&payment_method=transfer" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""
echo "\n=========================================="
echo "10. OBTENER FACTORES DE CONVERSIÓN"
echo "=========================================="
curl -s -X GET "$API_URL/currencies/factors" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "\n=========================================="
echo "11. OBTENER ESTADÍSTICAS DE USD"
echo "=========================================="
if [ ! -z "$USD_ID" ]; then
  curl -s -X GET "$API_URL/currencies/$USD_ID/statistics" \
    -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
fi

echo ""
echo "\n=========================================="
echo "12. VALIDAR CÓDIGO ISO 4217"
echo "=========================================="
curl -s -X POST "$API_URL/currencies/validate/iso-4217?code=USD" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "\n=========================================="
echo "13. VALIDAR CÓDIGO INVÁLIDO"
echo "=========================================="
curl -s -X POST "$API_URL/currencies/validate/iso-4217?code=XYZ" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "\n=========================================="
echo "✅ TEST FINALIZADO"
echo "=========================================="
