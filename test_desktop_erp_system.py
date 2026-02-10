"""
Script de prueba para el sistema Desktop ERP completo:
- Coins (Monedas)
- Coin History (Historial de tasas)
- Taxes (Impuestos)
- Tax Types (Tipos de impuesto)

Ejecutar: python3 test_desktop_erp_system.py
"""

import sys
sys.path.insert(0, '/home/muentes/devs/erp')

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

# Login y obtener token
def login():
    response = requests.post(f"{BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    if response.status_code == 200:
        data = response.json()
        print("✅ Login exitoso")
        return data["access_token"]
    else:
        print(f"❌ Error en login: {response.status_code}")
        print(response.text)
        return None

def test_coins(token):
    """Probar endpoints de coins"""
    print("\n=== TEST COINS ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Listar coins
    response = requests.get(f"{BASE_URL}/coins", headers=headers)
    if response.status_code == 200:
        coins = response.json()
        print(f"✅ GET /coins: {len(coins)} monedas encontradas")
        for coin in coins:
            print(f"   - {coin['code']}: {coin['name']} (factor_type={coin['factor_type']})")
    else:
        print(f"❌ Error GET /coins: {response.status_code}")
        print(response.text)

    # Obtener moneda base
    response = requests.get(f"{BASE_URL}/coins/base", headers=headers)
    if response.status_code == 200:
        base = response.json()
        print(f"✅ Moneda base: {base['code']} - {base['name']}")
    else:
        print(f"❌ Error GET /coins/base: {response.status_code}")

    # Obtener monedas activas
    response = requests.get(f"{BASE_URL}/coins/active", headers=headers)
    if response.status_code == 200:
        active = response.json()
        print(f"✅ Monedas activas: {len(active)}")
    else:
        print(f"❌ Error GET /coins/active: {response.status_code}")

def test_coin_history(token):
    """Probar endpoints de coin history"""
    print("\n=== TEST COIN HISTORY ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Listar coin history
    response = requests.get(f"{BASE_URL}/coin-history", headers=headers)
    if response.status_code == 200:
        history = response.json()
        print(f"✅ GET /coin-history: {len(history)} registros encontrados")
        if len(history) > 0:
            latest = history[0]
            print(f"   Último: {latest['currency_id']} sales={latest['sales_aliquot']} buy={latest['buy_aliquot']} {latest['register_date']}")
    else:
        print(f"❌ Error GET /coin-history: {response.status_code}")
        print(response.text)

def test_taxes(token):
    """Probar endpoints de taxes"""
    print("\n=== TEST TAXES ===")

    headers = {"Authorization": f"Bearer {token}"}

    # Listar tax types
    response = requests.get(f"{BASE_URL}/tax-types", headers=headers)
    if response.status_code == 200:
        tax_types = response.json()
        print(f"✅ GET /tax-types: {len(tax_types)} tipos de impuesto encontrados")
        for tt in tax_types:
            print(f"   - {tt['code']}: {tt['description']} (fiscal_pos={tt['fiscal_printer_position']})")
    else:
        print(f"❌ Error GET /tax-types: {response.status_code}")
        print(response.text)

    # Listar taxes
    response = requests.get(f"{BASE_URL}/taxes", headers=headers)
    if response.status_code == 200:
        taxes = response.json()
        print(f"✅ GET /taxes: {len(taxes)} códigos de impuesto encontrados")
        for tax in taxes:
            print(f"   - {tax['code']}: {tax['description']} ({tax['aliquot']}%)")
    else:
        print(f"❌ Error GET /taxes: {response.status_code}")
        print(response.text)

def main():
    print("🚀 Iniciando pruebas del sistema Desktop ERP")
    print("=" * 60)

    # Login
    token = login()
    if not token:
        return

    # Probar cada módulo
    test_coins(token)
    test_coin_history(token)
    test_taxes(token)

    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")

if __name__ == "__main__":
    main()
