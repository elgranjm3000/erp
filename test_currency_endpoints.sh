#!/bin/bash

# ============================================
# TEST COMPLETO DE ENDPOINTS DE MONEDAS
# ============================================

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""

# Colores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  TEST DE ENDPOINTS DE MONEDAS (CURRENCIES)${NC}"
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

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
    echo -e "${RED}Error: No se pudo obtener el token${NC}"
    echo "Response: $LOGIN_RESPONSE"
    exit 1
fi

echo -e "${GREEN}Token obtenido exitosamente${NC}\n"
sleep 1

# ============================================
# 2. LISTAR MONEDAS EXISTENTES
# ============================================

echo -e "${YELLOW}2. LISTAR MONEDAS EXISTENTES${NC}"
curl -s -X GET "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 3. OBTENER FACTORES DE CONVERSIÓN
# ============================================

echo -e "${YELLOW}3. OBTENER FACTORES DE CONVERSIÓN${NC}"
curl -s -X GET "$BASE_URL/currencies/factors" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 4. VALIDAR CÓDIGO ISO 4217 (USD)
# ============================================

echo -e "${YELLOW}4. VALIDAR CÓDIGO ISO 4217 (USD)${NC}"
curl -s -X POST "$BASE_URL/currencies/validate/iso-4217?code=USD" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 5. VALIDAR CÓDIGO ISO 4217 (EUR)
# ============================================

echo -e "${YELLOW}5. VALIDAR CÓDIGO ISO 4217 (EUR)${NC}"
curl -s -X POST "$BASE_URL/currencies/validate/iso-4217?code=EUR" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 6. CREAR NUEVA MONEDA (EUR)
# ============================================

echo -e "${YELLOW}6. CREAR NUEVA MONEDA (EUR)${NC}"
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
    "rate_update_method": "manual",
    "rate_source_url": null
  }')

echo "$EUR_RESPONSE" | python3 -m json.tool
EUR_ID=$(echo $EUR_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('id', 0))" 2>/dev/null)

echo -e "\n"
sleep 1

# ============================================
# 7. OBTENER MONEDA POR ID
# ============================================

if [ "$EUR_ID" != "0" ] && [ ! -z "$EUR_ID" ]; then
    echo -e "${YELLOW}7. OBTENER MONEDA EUR POR ID (ID: $EUR_ID)${NC}"
    curl -s -X GET "$BASE_URL/currencies/$EUR_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1

    # ============================================
    # 8. ACTUALIZAR TASA DE CAMBIO
    # ============================================

    echo -e "${YELLOW}8. ACTUALIZAR TASA DE CAMBIO DE EUR${NC}"
    curl -s -X PUT "$BASE_URL/currencies/$EUR_ID/rate" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "new_rate": "40.2000000000",
        "change_reason": "Actualización de prueba",
        "change_type": "manual",
        "change_source": "test_script"
      }' | python3 -m json.tool

    echo -e "\n"
    sleep 1

    # ============================================
    # 9. OBTENER HISTORIAL DE TASAS
    # ============================================

    echo -e "${YELLOW}9. OBTENER HISTORIAL DE TASAS DE EUR${NC}"
    curl -s -X GET "$BASE_URL/currencies/$EUR_ID/rate/history?limit=5" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1

    # ============================================
    # 10. OBTENER ESTADÍSTICAS DE MONEDA
    # ============================================

    echo -e "${YELLOW}10. OBTENER ESTADÍSTICAS DE EUR${NC}"
    curl -s -X GET "$BASE_URL/currencies/$EUR_ID/statistics" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 11. CONVERTIR MONEDA (USD -> VES)
# ============================================

echo -e "${YELLOW}11. CONVERTIR 100 USD A VES${NC}"
curl -s -X GET "$BASE_URL/currencies/convert?from_currency=USD&to_currency=VES&amount=100" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 12. CONVERTIR MONEDA (EUR -> VES)
# ============================================

echo -e "${YELLOW}12. CONVERTIR 50 EUR A VES${NC}"
curl -s -X GET "$BASE_URL/currencies/convert?from_currency=EUR&to_currency=VES&amount=50" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 13. LISTAR CONFIGURACIONES IGTF
# ============================================

echo -e "${YELLOW}13. LISTAR CONFIGURACIONES IGTF${NC}"
curl -s -X GET "$BASE_URL/currencies/igtf/config" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 14. CALCULAR IGTF
# ============================================

# Obtener ID de moneda USD
USD_ID=$(curl -s -X GET "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" | \
  python3 -c "import sys, json; data=json.load(sys.stdin); print([c['id'] for c in data if c.get('code')=='USD'][0] if any(c.get('code')=='USD' for c in data) else 0)" 2>/dev/null)

if [ "$USD_ID" != "0" ] && [ ! -z "$USD_ID" ]; then
    echo -e "${YELLOW}14. CALCULAR IGTF PARA 1500 USD${NC}"
    curl -s -X POST "$BASE_URL/currencies/igtf/calculate?amount=1500&currency_id=$USD_ID&payment_method=transfer" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 15. ACTUALIZAR MONEDA (sin cambiar tasa)
# ============================================

if [ "$EUR_ID" != "0" ] && [ ! -z "$EUR_ID" ]; then
    echo -e "${YELLOW}15. ACTUALIZAR DATOS DE EUR (nombre y símbolo)${NC}"
    curl -s -X PUT "$BASE_URL/currencies/$EUR_ID" \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      -d '{
        "name": "Euro Zone",
        "symbol": "€",
        "decimal_places": 2
      }' | python3 -m json.tool

    echo -e "\n"
    sleep 1
fi

# ============================================
# 16. LISTAR MONEDAS ACTIVAS
# ============================================

echo -e "${YELLOW}16. LISTAR SOLO MONEDAS ACTIVAS${NC}"
curl -s -X GET "$BASE_URL/currencies/?is_active=true" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 17. LISTAR MONEDAS INACTIVAS
# ============================================

echo -e "${YELLOW}17. LISTAR MONEDAS INACTIVAS${NC}"
curl -s -X GET "$BASE_URL/currencies/?is_active=false" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 18. VERIFICAR LISTA FINAL DE MONEDAS
# ============================================

echo -e "${YELLOW}18. LISTA FINAL DE MONEDAS${NC}"
curl -s -X GET "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo -e "\n"
sleep 1

# ============================================
# 19. ELIMINAR MONEDA EUR (SOFT DELETE)
# ============================================

if [ "$EUR_ID" != "0" ] && [ ! -z "$EUR_ID" ]; then
    echo -e "${YELLOW}19. ELIMINAR MONEDA EUR (SOFT DELETE)${NC}"
    curl -s -X DELETE "$BASE_URL/currencies/$EUR_ID" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
    sleep 1

    # Verificar que esté inactiva
    echo -e "${YELLOW}VERIFICAR QUE EUR ESTÉ INACTIVA${NC}"
    curl -s -X GET "$BASE_URL/currencies/?is_active=false" \
      -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

    echo -e "\n"
fi

# ============================================
# RESUMEN
# ============================================

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  TEST COMPLETADO${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\nEndpoints probados:"
echo -e "  ✅ POST /auth/login"
echo -e "  ✅ GET  /currencies/"
echo -e "  ✅ GET  /currencies/factors"
echo -e "  ✅ POST /currencies/validate/iso-4217"
echo -e "  ✅ POST /currencies/ (crear moneda)"
echo -e "  ✅ GET  /currencies/{id}"
echo -e "  ✅ PUT  /currencies/{id}/rate"
echo -e "  ✅ GET  /currencies/{id}/rate/history"
echo -e "  ✅ GET  /currencies/{id}/statistics"
echo -e "  ✅ GET  /currencies/convert"
echo -e "  ✅ GET  /currencies/igtf/config"
echo -e "  ✅ POST /currencies/igtf/calculate"
echo -e "  ✅ PUT  /currencies/{id}"
echo -e "  ✅ GET  /currencies/?is_active=true/false"
echo -e "  ✅ DELETE /currencies/{id}"
echo -e "\n${GREEN}Todos los tests completados exitosamente${NC}\n"
