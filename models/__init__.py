# Models package - evitar importaciones circulares
import sys
import os

# Cargar models.py directamente en sys.modules para evitar circular import
current_dir = os.path.dirname(__file__)
models_path = os.path.join(current_dir, '..', 'models.py')

if 'models_file' not in sys.modules:
    import importlib.util
    spec = importlib.util.spec_from_file_location("models_file", models_path)
    models_file = importlib.util.module_from_spec(spec)
    sys.modules['models_file'] = models_file
    spec.loader.exec_module(models_file)

# Exportar las clases principales desde models.py
Base = sys.modules['models_file'].Base
User = sys.modules['models_file'].User
Company = sys.modules['models_file'].Company
Product = sys.modules['models_file'].Product
Category = sys.modules['models_file'].Category
Unit = sys.modules['models_file'].Unit
Warehouse = sys.modules['models_file'].Warehouse
WarehouseProduct = sys.modules['models_file'].WarehouseProduct
InventoryMovement = sys.modules['models_file'].InventoryMovement
Customer = sys.modules['models_file'].Customer
Supplier = sys.modules['models_file'].Supplier
Invoice = sys.modules['models_file'].Invoice
InvoiceItem = sys.modules['models_file'].InvoiceItem
Purchase = sys.modules['models_file'].Purchase
PurchaseItem = sys.modules['models_file'].PurchaseItem
ProductPrice = sys.modules['models_file'].ProductPrice
ExchangeRateHistory = sys.modules['models_file'].ExchangeRateHistory
CoinHistory = sys.modules['models_file'].CoinHistory  # ✅ SISTEMA ESCRITORIO: Historial de monedas
ProductPriceHistory = sys.modules['models_file'].ProductPriceHistory
InvoiceRateHistory = sys.modules['models_file'].InvoiceRateHistory

# ✅ AUDITORÍA: Logs de seguridad
AuditLog = sys.modules['models_file'].AuditLog

# ✅ SISTEMA ESCRITORIO: Impuestos
TaxType = sys.modules['models_file'].TaxType
Tax = sys.modules['models_file'].Tax

# ✅ SISTEMA ESCRITORIO: Exportar modelos de operaciones de venta
SalesOperation = sys.modules['models_file'].SalesOperation
SalesOperationCoin = sys.modules['models_file'].SalesOperationCoin
SalesOperationDetail = sys.modules['models_file'].SalesOperationDetail
SalesOperationDetailCoin = sys.modules['models_file'].SalesOperationDetailCoin
SalesOperationTax = sys.modules['models_file'].SalesOperationTax
SalesOperationTaxCoin = sys.modules['models_file'].SalesOperationTaxCoin

# Importar modelos de currency_config (sistema venezolano)
from models.currency_config import Currency, IGTFConfig, CurrencyRateHistory

# Importar modelo de tasas diarias
from models.daily_rates import DailyRate

__all__ = [
    'Base',
    'User',
    'Company',
    'Product',
    'Category',
    'Unit',
    'Warehouse',
    'WarehouseProduct',
    'InventoryMovement',
    'Customer',
    'Supplier',
    'Invoice',
    'InvoiceItem',
    'Purchase',
    'PurchaseItem',
    'ProductPrice',
    'Currency',
    'ExchangeRateHistory',
    'CoinHistory',
    'ProductPriceHistory',
    'InvoiceRateHistory',
    'IGTFConfig',
    'CurrencyRateHistory',
    'DailyRate',
    # ✅ AUDITORÍA: Logs de seguridad
    'AuditLog',
    # ✅ SISTEMA ESCRITORIO: Impuestos
    'TaxType',
    'Tax',
    # ✅ SISTEMA ESCRITORIO: Operaciones de venta
    'SalesOperation',
    'SalesOperationCoin',
    'SalesOperationDetail',
    'SalesOperationDetailCoin',
    'SalesOperationTax',
    'SalesOperationTaxCoin',
]

