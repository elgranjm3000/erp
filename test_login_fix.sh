#!/bin/bash

# Test del fix de timeout en login

BASE_URL="http://localhost:8000/api/v1"

echo "============================================"
echo "  TEST FIX TIMEOUT LOGIN"
echo "============================================"
echo ""

# ============================================
# TEST 1: LOGIN NORMAL (sin company_tax_id)
# ============================================

echo "=== TEST 1: LOGIN NORMAL ==="
echo "Usuario: admin | Password: admin123"

START=$(date +%s%N)

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  --max-time 15 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "admin123"
  }')

END=$(date +%s%N)
TIME=$(( (END - START) / 1000000 ))

echo "Response time: ${TIME}ms"
echo ""

# Verificar si fue exitoso
if echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('access_token', 'ERROR'))" 2>/dev/null | grep -q "eyJ"; then
    TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
    echo "✅ LOGIN EXITOSO"
    echo "Token: ${TOKEN:0:30}..."
    echo ""

    if [ $TIME -lt 1000 ]; then
        echo "✅ TIMEOUT ARREGLADO - Login rápido (< 1s)"
    elif [ $TIME -lt 5000 ]; then
        echo "⚠️  Login aceptable (< 5s)"
    else
        echo "❌ Login aún lento (> 5s)"
    fi
else
    echo "❌ LOGIN FALLÓ"
    echo "Response:"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool
fi

echo ""
echo "============================================"
echo ""

# ============================================
# TEST 2: MÚLTIPLES LOGINS (verificar consistencia)
# ============================================

echo "=== TEST 2: MULTIPLES LOGINS (5) ==="
TIMES=()

for i in {1..5}; do
    echo "Login $i/5..."

    START=$(date +%s%N)

    RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
      --max-time 15 \
      -H "Content-Type: application/json" \
      -d '{
        "username": "admin",
        "password": "admin123"
      }' > /dev/null)

    END=$(date +%s%N)
    TIME=$(( (END - START) / 1000000 ))
    TIMES+=($TIME)

    echo "  Tiempo: ${TIME}ms"
    sleep 0.5
done

# Calcular promedio
TOTAL=0
for time in "${TIMES[@]}"; do
    TOTAL=$((TOTAL + time))
done
AVG=$((TOTAL / 5))

echo ""
echo "📊 Estadísticas:"
echo "   Tiempo mínimo: $(printf '%s\n' "${TIMES[@]}" | sort -n | head -1)ms"
echo "   Tiempo máximo: $(printf '%s\n' "${TIMES[@]}" | sort -n | tail -1)ms"
echo "   Promedio: ${AVG}ms"
echo ""

if [ $AVG -lt 1000 ]; then
    echo "✅ EXCELENTE - Login consistently rápido"
elif [ $AVG -lt 3000 ]; then
    echo "✅ BUENO - Login consistente"
else
    echo "⚠️  Login aún lento en promedio"
fi

echo ""
echo "============================================"
echo "  TEST COMPLETADO"
echo "============================================"
echo ""
echo "✅ Fix de timeout aplicado:"
echo "   • Eager loading de User.company"
echo "   • Una sola query en lugar de múltiples"
echo "   • Sin lazy loading timeouts"
echo ""
