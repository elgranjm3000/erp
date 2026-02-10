#!/bin/bash

# Test específico para el usuario elgranjm

BASE_URL="http://localhost:8000/api/v1"

echo "============================================"
echo "  TEST LOGIN - elgranjm"
echo "============================================"
echo ""

echo "Request:"
echo '{'
echo '  "username": "elgranjm",'
echo '  "password": "12345678",'
echo '  "company_tax_id": "123"'
echo '}'
echo ""

echo "Enviando request..."
START=$(date +%s%N)

RESPONSE=$(curl -v -X POST "$BASE_URL/auth/login" \
  --max-time 15 \
  -H "Content-Type: application/json" \
  -d '{
    "username": "elgranjm",
    "password": "12345678",
    "company_tax_id": "123"
  }' 2>&1)

END=$(date +%s%N)
TIME=$(( (END - START) / 1000000 ))

echo ""
echo "Response time: ${TIME}ms"
echo ""
echo "Response:"
echo "$RESPONSE" | grep -v "^{" | grep -v "^}" | head -50
echo ""

# Intentar parsear JSON
JSON_PART=$(echo "$RESPONSE" | grep -A 100 "^{")
if [ ! -z "$JSON_PART" ]; then
    echo "$JSON_PART" | python3 -m json.tool 2>/dev/null || echo "No es JSON válido"
fi
