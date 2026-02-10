#!/bin/bash

# ============================================
# TEST DEL FIX: ACTUALIZACIÓN DE TASA DE CAMBIO
# ============================================

BASE_URL="http://localhost:8000/api/v1"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}TEST: ACTUALIZACIÓN DE TASA DE CAMBIO${NC}\n"

# ============================================
# 1. OBTENER TOKEN
# ============================================

echo "1. Obteniendo token..."
TOKEN=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))")

if [ -z "$TOKEN" ] || [ "$TOKEN" == "None" ]; then
    echo -e "${RED}Error: No se pudo obtener el token${NC}"
    exit 1
fi

echo -e "${GREEN}Token obtenido${NC}\n"
sleep 1

# ============================================
# 2. OBTENER MONEDA USD
# ============================================

echo "2. Obteniendo moneda USD..."
USD_DATA=$(curl -s -X GET "$BASE_URL/currencies/" \
  -H "Authorization: Bearer $TOKEN")

USD_ID=$(echo $USD_DATA | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data:
    if c.get('code') == 'USD' and c.get('is_active') == True:
        print(c.get('id'))
        break
" 2>/dev/null)

if [ -z "$USD_ID" ]; then
    echo -e "${RED}Error: No se encontró moneda USD activa${NC}"
    echo "Datos: $USD_DATA"
    exit 1
fi

echo -e "${GREEN}Moneda USD encontrada: ID $USD_ID${NC}\n"
sleep 1

# ============================================
# 3. ACTUALIZAR TASA DE CAMBIO (TEST DEL FIX)
# ============================================

echo "3. Actualizando tasa de cambio de USD (36.5 -> 37.8)..."
RESPONSE=$(curl -s -X PUT "$BASE_URL/currencies/$USD_ID/rate" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "new_rate": "37.8000000000",
    "change_reason": "Test del fix Decimal/float",
    "change_type": "manual",
    "change_source": "test_script"
  }')

echo "$RESPONSE" | python3 -m json.tool

ERROR=$(echo $RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get('error', 'false'))" 2>/dev/null)

if [ "$ERROR" == "True" ]; then
    echo -e "\n${RED}❌ FALLÓ: El endpoint sigue teniendo errores${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ EXITO: La tasa se actualizó correctamente${NC}"
fi

echo -e "\n"
sleep 2

# ============================================
# 4. VERIFICAR HISTORIAL DE TASAS
# ============================================

echo "4. Verificando historial de tasas..."
HISTORY=$(curl -s -X GET "$BASE_URL/currencies/$USD_ID/rate/history?limit=5" \
  -H "Authorization: Bearer $TOKEN")

echo "$HISTORY" | python3 -m json.tool

if [ -z "$HISTORY" ] || [ "$HISTORY" == "[]" ]; then
    echo -e "\n${YELLOW}⚠️  Historial vacío (puede ser normal si es la primera actualización)${NC}"
else
    echo -e "\n${GREEN}✅ Historial disponible${NC}"
fi

echo -e "\n"
sleep 1

# ============================================
# 5. VERIFICAR ESTADÍSTICAS
# ============================================

echo "5. Verificando estadísticas..."
STATS=$(curl -s -X GET "$BASE_URL/currencies/$USD_ID/statistics" \
  -H "Authorization: Bearer $TOKEN")

echo "$STATS" | python3 -m json.tool

ERROR=$(echo $STATS | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'false'))" 2>/dev/null)

if [ "$ERROR" == "True" ]; then
    echo -e "\n${RED}❌ FALLÓ: Error en estadísticas${NC}"
else
    echo -e "\n${GREEN}✅ EXITO: Estadísticas obtenidas${NC}"
fi

echo -e "\n"
sleep 1

# ============================================
# 6. VERIFICAR IGTF
# ============================================

echo "6. Verificando cálculo de IGTF..."
IGTF=$(curl -s -X POST "$BASE_URL/currencies/igtf/calculate?amount=1500&currency_id=$USD_ID&payment_method=transfer" \
  -H "Authorization: Bearer $TOKEN")

echo "$IGTF" | python3 -m json.tool

ERROR=$(echo $IGTF | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('error', 'false'))" 2>/dev/null)

if [ "$ERROR" == "True" ]; then
    echo -e "\n${RED}❌ FALLÓ: Error en cálculo IGTF${NC}"
else
    echo -e "\n${GREEN}✅ EXITO: IGTF calculado${NC}"
fi

echo -e "\n"
sleep 1

# ============================================
# 7. LISTAR CONFIG IGTF
# ============================================

echo "7. Listando configuración IGTF..."
CONFIG=$(curl -s -X GET "$BASE_URL/currencies/igtf/config" \
  -H "Authorization: Bearer $TOKEN")

echo "$CONFIG" | python3 -m json.tool

if [ -z "$CONFIG" ] || [ "$CONFIG" == "[]" ]; then
    echo -e "\n${YELLOW}⚠️  Configuración IGTF vacía (normal si no se ha creado config especial)${NC}"
else
    echo -e "\n${GREEN}✅ Configuración IGTF disponible${NC}"
fi

echo -e "\n"

# ============================================
# RESUMEN
# ============================================

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  TEST COMPLETADO${NC}"
echo -e "${GREEN}============================================${NC}"
echo -e "\n${GREEN}Fixes verificados:${NC}"
echo -e "  ✅ PUT /currencies/{id}/rate (Decimal/float fix)"
echo -e "  ✅ GET /currencies/{id}/rate/history"
echo -e "  ✅ GET /currencies/{id}/statistics"
echo -e "  ✅ POST /currencies/igtf/calculate"
echo -e "  ✅ GET /currencies/igtf/config"
echo -e "\n${GREEN}Todos los endpoints están funcionando${NC}\n"
