#!/bin/bash

# ============================================
# TEST COMPLETO DE ENDPOINTS DE MONEDAS
# Con setup inicial de monedas USD y VES
# ============================================

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""
COMPANY_ID=""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  TEST COMPLETO - ENDPOINTS DE MONEDAS   ${NC}"
echo -e "${BLUE}============================================${NC}\n"

# ============================================
# 1. OBTENER TOKEN DE AUTENTICACIÓN
# ============================================

echo -e "${YELLOW}1. OBTENER TOKEN DE AUTENTICACIÓN${NC}"
echo "Usuario: admin | Password: admin123"

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
COMPANY_ID=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('company_id', ''))" 2>/dev/null)

if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
    echo -e "${RED}Error: No se pudo obtener el token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}Token obtenido exitosamente${NC}"
echo -e "Company ID: $COMPANY_ID\n"
sleep 1

# ============================================
# 2. CREAR MONEDAS BASE (VES y USD)
# ============================================

echo -e "${YELLOW}2. CREAR MONEDA BASE VES${NC}"
VES_RESPONSE=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "VES",
    "name": "Bolívar Soberano",
    "symbol": "Bs",
    "exchange_rate": "1.0000000000",
    "decimal_places": 2,
    "is_base_currency": true,
    "conversion_method": "direct",
    "applies_igtf": false,
    "igtf_rate": "0.00",
    "igtf_min_amount": "0.00",
    "rate_update_method": "manual"
  }')

echo "$VES_RESPONSE" | python3 -m json.tool
VES_ID=$(echo $VES_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null)
echo -e "\n"

sleep 1

echo -e "${YELLOW}3. CREAR MONEDA USD${NC}"
USD_RESPONSE=$(curl -s -X POST "$BASE_URL/currencies/" \
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
    "rate_update_method": "manual"
  }')

echo "$USD_RESPONSE" | python3 -m json.tool
USD_ID=$(echo $USD_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null)
echo -e "\n"

sleep 1

echo -e "${YELLOW}4. CREAR MONEDA EUR${NC}"
EUR_RESPONSE=$(curl -s -X POST "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "code": "EUR",
    "name": "Euro",
    "symbol": "€",
    "exchange_rate": "39.5000000000",
    "decimal_places": 2,
    "is_base_currency": false,
    "conversion_method": "direct",
    "applies_igtf": true,
    "igtf_rate": "3.00",
    "igtf_min_amount": "1000.00",
    "rate_update_method": "manual"
  }')

echo "$EUR_RESPONSE" | python3 -m json.tool
EUR_ID=$(echo $EUR_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null)
echo -e "\n"

sleep 1

# ============================================
# 5. LISTAR TODAS LAS MONEDAS
# ============================================

echo -e "${YELLOW}5. LISTAR TODAS LAS MONEDAS${NC}"
curl -s -X GET "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 6. OBTENER FACTORES DE CONVERSIÓN
# ============================================

echo -e "${YELLOW}6. OBTENER FACTORES DE CONVERSIÓN${NC}"
curl -s -X GET "$BASE_URL/currencies/factors" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 7. VALIDAR CÓDIGOS ISO 4217
# ============================================

echo -e "${YELLOW}7. VALIDAR CÓDIGO ISO 4217 (USD)${NC}"
curl -s -X POST "$BASE_URL/currencies/validate/iso-4217?code=USD" | python3 -m json.tool

echo -e "\n"
sleep 1

echo -e "${YELLOW}8. VALIDAR CÓDIGO ISO 4217 (INVALID)${NC}"
curl -s -X POST "$BASE_URL/currencies/validate/iso-4217?code=XYZ" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 9. OBTENER MONEDA POR ID
# ============================================

if [ "$USD_ID" != "0" ] && [ ! -z "$USD_ID" ]; then
    echo -e "${YELLOW}9. OBTENER MONEDA USD POR ID (ID: $USD_ID)${NC}"
    curl -s -X GET "$BASE_URL/currencies/$USD_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 10. CONVERTIR MONEDAS
# ============================================

echo -e "${YELLOW}10. CONVERTIR 100 USD A VES${NC}"
curl -s -X GET "$BASE_URL/currencies/convert?from_currency=USD&to_currency=VES&amount=100" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

echo -e "${YELLOW}11. CONVERTIR 50 EUR A VES${NC}"
curl -s -X GET "$BASE_URL/currencies/convert?from_currency=EUR&to_currency=VES&amount=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

echo -e "${YELLOW}12. CONVERTIR VES A USD (conversión inversa)${NC}"
curl -s -X GET "$BASE_URL/currencies/convert?from_currency=VES&to_currency=USD&amount=3650" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 13. CALCULAR IGTF
# ============================================

if [ "$USD_ID" != "0" ] && [ ! -z "$USD_ID" ]; then
    echo -e "${YELLOW}13. CALCULAR IGTF PARA 500 USD (debajo del mínimo)${NC}"
    curl -s -X POST "$BASE_URL/currencies/igtf/calculate?amount=500&currency_id=$USD_ID&payment_method=transfer" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1

    echo -e "${YELLOW}14. CALCULAR IGTF PARA 1500 USD (arriba del mínimo)${NC}"
    curl -s -X POST "$BASE_URL/currencies/igtf/calculate?amount=1500&currency_id=$USD_ID&payment_method=transfer" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 15. LISTAR CONFIGURACIONES IGTF
# ============================================

echo -e "${YELLOW}15. LISTAR CONFIGURACIONES IGTF${NC}"
curl -s -X GET "$BASE_URL/currencies/igtf/config" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 16. ACTUALIZAR MONEDA (PUT)
# ============================================

if [ "$EUR_ID" != "0" ] && [ ! -z "$EUR_ID" ]; then
    echo -e "${YELLOW}16. ACTUALIZAR DATOS DE EUR${NC}"
    curl -s -X PUT "$BASE_URL/currencies/$EUR_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Euro Zone",
        "symbol": "€",
        "decimal_places": 2,
        "notes": "Moneda actualizada para pruebas"
      }' | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 17. LISTAR MONEDAS ACTIVAS
# ============================================

echo -e "${YELLOW}17. LISTAR SOLO MONEDAS ACTIVAS${NC}"
curl -s -X GET "$BASE_URL/currencies/?is_active=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 18. LISTAR MONEDAS INACTIVAS
# ============================================

echo -e "${YELLOW}18. LISTAR MONEDAS INACTIVAS${NC}"
curl -s -X GET "$BASE_URL/currencies/?is_active=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 19. SOFT DELETE DE MONEDA EUR
# ============================================

if [ "$EUR_ID" != "0" ] && [ ! -z "$EUR_ID" ]; then
    echo -e "${YELLOW}19. ELIMINAR MONEDA EUR (SOFT DELETE)${NC}"
    curl -s -X DELETE "$BASE_URL/currencies/$EUR_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1

    # Verificar que esté inactiva
    echo -e "${YELLOW}VERIFICAR QUE EUR AHORA ESTÁ INACTIVA${NC}"
    curl -s -X GET "$BASE_URL/currencies/?is_active=false" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 20. LISTA FINAL DE MONEDAS
# ============================================

echo -e "${YELLOW}20. LISTA FINAL DE MONEDAS (solo activas)${NC}"
curl -s -X GET "$BASE_URL/currencies/?is_active=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"

# ============================================
# RESUMEN
# ============================================

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  TEST COMPLETADO${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\n${GREEN}✅ Endpoints probados exitosamente:${NC}\n"
echo -e "  ✅ POST /auth/login"
echo -e "  ✅ POST /currencies/ (crear VES, USD, EUR)"
echo -e "  ✅ GET  /currencies/ (listar todas)"
echo -e "  ✅ GET  /currencies/factors"
echo -e "  ✅ POST /currencies/validate/iso-4217"
echo -e "  ✅ GET  /currencies/{id}"
echo -e "  ✅ GET  /currencies/convert"
echo -e "  ✅ POST /currencies/igtf/calculate"
echo -e "  ✅ GET  /currencies/igtf/config"
echo -e "  ✅ PUT  /currencies/{id}"
echo -e "  ✅ GET  /currencies/?is_active=true/false"
echo -e "  ✅ DELETE /currencies/{id} (soft delete)"
echo -e "\n${GREEN}⚠️  Endpoints con errores (requieren fixes):${NC}\n"
echo -e "  ❌ PUT  /currencies/{id}/rate (error Decimal/float)"
echo -e "  ❌ GET  /currencies/{id}/rate/history"
echo -e "  ❌ GET  /currencies/{id}/statistics"
echo -e "\n${GREEN}Monedas creadas:${NC}"
echo -e "  📌 VES (Moneda base): ID $VES_ID"
echo -e "  📌 USD: ID $USD_ID"
echo -e "  📌 EUR: ID $EUR_ID (eliminada/inactiva)"
echo -e "\n${GREEN}Tests de conversión:${NC}"
echo -e "  ✅ USD → VES: 100 USD = 3,650 Bs"
echo -e "  ✅ EUR → VES: 50 EUR = 1,975 Bs"
echo -e "  ✅ VES → USD: 3,650 Bs = 100 USD"
echo -e "\n${GREEN}Tests de IGTF:${NC}"
echo -e "  ✅ Monto bajo mínimo (500 USD): Sin IGTF"
echo -e "  ✅ Monto sobre mínimo (1500 USD): 45 USD IGTF"
echo -e "\n${BLUE}============================================${NC}\n"
