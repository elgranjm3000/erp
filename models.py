from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Company(Base):
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    legal_name = Column(String(150), nullable=False)
    tax_id = Column(String(20), unique=True, nullable=False, index=True)  # RIF/NIT
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(String(300))
    logo_url = Column(String(255))

    # Configuraciones específicas de la empresa
    currency = Column(String(3), default="USD")  # USD, VES, etc.
    exchange_rate = Column(Float, default=1.0)  # Tasa de cambio USD->VES
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")

    # Configuraciones de facturación
    invoice_prefix = Column(String(10), default="INV")  # INV, FAC, etc.
    next_invoice_number = Column(Integer, default=1)
    next_control_number = Column(Integer, default=1)  # ✅ VENEZUELA: Número de control

    # ✅ VENEZUELA: Información fiscal para SENIAT
    fiscal_address = Column(String(300))  # Dirección fiscal exacta para facturas
    taxpayer_type = Column(String(20), default='ordinario')  # 'contribuyente especial', 'ordinario'
    seniat_certificate_number = Column(String(30))  # Certificado SENIAT
    iva_retention_agent = Column(Boolean, default=False)  # Agente de retención IVA
    islr_retention_agent = Column(Boolean, default=False)  # Agente de retención ISLR

    # ✅ VENEZUELA: Información de contacto para facturas
    invoice_contact_name = Column(String(100))
    invoice_contact_phone = Column(String(20))
    invoice_contact_email = Column(String(100))

    # ✅ VENEZUELA: Tasas de retención (configurables por empresa)
    iva_retention_rate_75 = Column(Float, default=75.0)  # Umbral para 75%
    iva_retention_rate_100 = Column(Float, default=100.0)  # Umbral para 100%
    islr_retention_rate_1 = Column(Float, default=1.0)  # Umbral para 1%
    islr_retention_rate_2 = Column(Float, default=2.0)  # Umbral para 2%
    islr_retention_rate_3 = Column(Float, default=3.0)  # Umbral para 3%

    # ✅ VENEZUELA: Monto mínimo para requerir RIF del cliente (en moneda local)
    require_customer_tax_id_threshold = Column(Float, default=0.0)  # 0 = siempre requerir

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    users = relationship("User", back_populates="company")
    warehouses = relationship("Warehouse", back_populates="company")
    products = relationship("Product", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")
    invoices = relationship("Invoice", back_populates="company")
    purchases = relationship("Purchase", back_populates="company")
    currencies = relationship("Currency")  # ✅ MONEDAS
    units = relationship("Unit")  # ✅ UNIDADES DE MEDIDA

# Cliente
class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(60), index=True)
    email = Column(String(60), index=True)  # ✅ CORREGIDO: No unique globalmente
    phone = Column(String(11))
    address = Column(String(200))
    tax_id = Column(String(20))  # ✅ AGREGADO: RIF/CI del cliente
    latitude = Column(Float, nullable=True)  # ✅ UBICACIÓN: Latitud para mapa
    longitude = Column(Float, nullable=True)  # ✅ UBICACIÓN: Longitud para mapa

    # Relaciones
    invoices = relationship("Invoice", back_populates="customer")
    company = relationship("Company", back_populates="customers")

# Factura
class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'))

    # Numeración por empresa
    invoice_number = Column(String(20), index=True)
    control_number = Column(String(20), index=True)  # ✅ VENEZUELA: Número de control SENIAT

    # ✅ MONEDA: Moneda y tasa de cambio de la factura
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    exchange_rate = Column(Float, nullable=True)  # Tasa de cambio usada (para registro histórico)

    date = Column(DateTime, default=func.now())
    due_date = Column(DateTime, default=func.now())
    total_amount = Column(Float)
    status = Column(String(60))  # 'presupuesto', 'factura', 'nota_credito', 'devolucion'
    discount = Column(Float, default=0.0)
    notes = Column(Text)

    # ✅ VENEZUELA: Información fiscal
    transaction_type = Column(String(20), default='contado')  # 'contado', 'credito'
    payment_method = Column(String(30))  # 'efectivo', 'transferencia', 'debito', 'credito', 'zelle', 'pago_movil'
    credit_days = Column(Integer, default=0)

    # ✅ VENEZUELA: Impuestos (IVA)
    iva_percentage = Column(Float, default=16.0)  # 16%, 8%, 0% (exento)
    iva_amount = Column(Float, default=0.0)
    taxable_base = Column(Float, default=0.0)  # Base imponible
    exempt_amount = Column(Float, default=0.0)  # Monto exento de IVA

    # ✅ VENEZUELA: Retenciones
    iva_retention = Column(Float, default=0.0)  # 75% o 100% del IVA
    iva_retention_percentage = Column(Float, default=0.0)  # 75% o 100%
    islr_retention = Column(Float, default=0.0)  # Retención ISLR (1%, 2%, 3%)
    islr_retention_percentage = Column(Float, default=0.0)

    # ✅ VENEZUELA: Timado Fiscal
    stamp_tax = Column(Float, default=0.0)  # 1% del total

    # ✅ VENEZUELA: Totales desglosados
    subtotal = Column(Float, default=0.0)  # Antes de impuestos
    total_with_taxes = Column(Float, default=0.0)  # Incluyendo todos los impuestos

    # ✅ VENEZUELA: Datos adicionales para notas de crédito/débito
    reference_invoice_number = Column(String(30))  # Factura original (para NC/ND)
    reference_control_number = Column(String(20))  # Número de control original
    refund_reason = Column(Text)  # Motivo de la NC/ND

    # Información de contacto del cliente en la factura
    customer_phone = Column(String(20))
    customer_address = Column(String(300))

    # Relaciones
    customer = relationship("Customer", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")
    company = relationship("Company", back_populates="invoices")
    warehouse = relationship("Warehouse")
    currency = relationship("Currency")  # ✅ MONEDA

# Detalle de la Factura
class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    total_price = Column(Float)

    # ✅ VENEZUELA: Información fiscal por item
    tax_rate = Column(Float, default=16.0)  # Tasa impositiva (16%, 8%, 0%)
    tax_amount = Column(Float, default=0.0)  # IVA por item
    is_exempt = Column(Boolean, default=False)  # Si el item está exento de IVA

    invoice = relationship("Invoice", back_populates="invoice_items")
    product = relationship("Product")

# Movimiento de Crédito (para notas de crédito y devoluciones de VENTAS)
class CreditMovement(Base):
    __tablename__ = 'credit_movements'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    amount = Column(Float)
    movement_type = Column(String(60))  # 'nota_credito' o 'devolucion'
    reason = Column(Text)  # ✅ Motivo de la nota de crédito
    date = Column(DateTime, default=func.now())

    invoice = relationship("Invoice")

# ✅ VENEZUELA: Movimiento de Crédito para COMPRAS (Notas de crédito de proveedores)
class PurchaseCreditMovement(Base):
    __tablename__ = 'purchase_credit_movements'

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey('purchases.id'))
    amount = Column(Float)
    movement_type = Column(String(60))  # 'nota_credito' o 'devolucion'
    reason = Column(Text)  # Motivo de la nota de crédito
    date = Column(DateTime, default=func.now())

    # ✅ Referencia a la compra original
    reference_purchase_number = Column(String(30))  # Número de compra original
    reference_control_number = Column(String(20))  # Número de control original

    # ✅ Información de reversión de stock
    stock_reverted = Column(Boolean, default=False)  # Si se revirtió el stock
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)  # Almacén afectado

    purchase = relationship("Purchase")
    warehouse = relationship("Warehouse")

# Categoría de producto
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)  # ✅ AGREGADO
    name = Column(String(60), index=True)
    description = Column(String(200))

    products = relationship("Product", back_populates="category")
    company = relationship("Company")  # ✅ AGREGADO

# Producto
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(60), index=True)
    description = Column(String(200))
    price = Column(Integer)
    quantity = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'))
    sku = Column(String(50), index=True)  # ✅ AGREGADO

    # Relaciones
    company = relationship("Company", back_populates="products")
    category = relationship("Category", back_populates="products")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    warehouses = relationship("Warehouse", secondary="warehouse_products", back_populates="products")    
    purchase_items = relationship("PurchaseItem", back_populates="product")

# Almacén
class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(60), index=True)
    location = Column(String(200))

    # Relaciones
    company = relationship("Company", back_populates="warehouses")
    products = relationship("Product", secondary="warehouse_products", back_populates="warehouses")
    purchases = relationship('Purchase', back_populates='warehouse')

# Relación entre Almacenes y Productos (Stock por Almacén)
class WarehouseProduct(Base):
    __tablename__ = 'warehouse_products'

    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'), primary_key=True)
    stock = Column(Integer)

# Movimiento de Inventario (Entrada, Salida)
class InventoryMovement(Base):
    __tablename__ = 'inventory_movements'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)
    invoice_id = Column(Integer, nullable=True)
    movement_type = Column(String(60))  # Puede ser 'entrada', 'salida'
    quantity = Column(Integer)
    timestamp = Column(DateTime, default=func.now())
    description = Column(Text)

    product = relationship("Product", back_populates="inventory_movements")
    warehouse = relationship("Warehouse")

class Supplier(Base):
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(60), nullable=False)
    contact = Column(String(30), nullable=True)
    address = Column(String(200), nullable=True)
    tax_id = Column(String(20))  # ✅ AGREGADO: RIF del proveedor

    # Relaciones
    purchases = relationship("Purchase", back_populates="supplier")
    company = relationship("Company", back_populates="suppliers")  # ✅ CORREGIDO

class Purchase(Base):
    __tablename__ = "purchases"

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)

    # Numeración por empresa
    purchase_number = Column(String(20), index=True)  # ✅ AGREGADO
    invoice_number = Column(String(30), index=True)  # ✅ Número de factura del proveedor
    control_number = Column(String(20), index=True)  # ✅ VENEZUELA: Número de control

    # ✅ MONEDA: Moneda y tasa de cambio de la compra
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    exchange_rate = Column(Float, nullable=True)  # Tasa de cambio usada (para registro histórico)

    date = Column(DateTime, default=func.now())
    due_date = Column(DateTime, default=func.now())
    total_amount = Column(Float, default=0.0)
    status = Column(String(60), default="pending")  # 'pending', 'received', 'cancelled'
    discount = Column(Float, default=0.0)
    notes = Column(Text)

    # ✅ VENEZUELA: Información fiscal
    transaction_type = Column(String(20), default='contado')  # 'contado', 'credito'
    payment_method = Column(String(30))  # 'efectivo', 'transferencia', 'debito', 'credito', 'zelle', 'pago_movil'
    credit_days = Column(Integer, default=0)

    # ✅ VENEZUELA: Impuestos (IVA)
    iva_percentage = Column(Float, default=16.0)  # 16%, 8%, 0% (exento)
    iva_amount = Column(Float, default=0.0)
    taxable_base = Column(Float, default=0.0)  # Base imponible
    exempt_amount = Column(Float, default=0.0)  # Monto exento de IVA

    # ✅ VENEZUELA: Retenciones
    iva_retention = Column(Float, default=0.0)  # 75% o 100% del IVA
    iva_retention_percentage = Column(Float, default=0.0)  # 75% o 100%
    islr_retention = Column(Float, default=0.0)  # Retención ISLR (1%, 2%, 3%)
    islr_retention_percentage = Column(Float, default=0.0)

    # ✅ VENEZUELA: Timado Fiscal
    stamp_tax = Column(Float, default=0.0)  # 1% del total

    # ✅ VENEZUELA: Totales desglosados
    subtotal = Column(Float, default=0.0)  # Antes de impuestos
    total_with_taxes = Column(Float, default=0.0)  # Incluyendo todos los impuestos

    # ✅ VENEZUELA: Datos adicionales para notas de crédito/débito
    reference_purchase_number = Column(String(30))  # Compra original (para NC/ND)
    reference_control_number = Column(String(20))  # Número de control original
    refund_reason = Column(Text)  # Motivo de la NC/ND

    # Información de contacto del proveedor
    supplier_phone = Column(String(20))
    supplier_address = Column(String(300))

    # Relaciones
    company = relationship("Company", back_populates="purchases")
    supplier = relationship("Supplier", back_populates="purchases")
    warehouse = relationship("Warehouse", back_populates="purchases")
    currency = relationship("Currency")  # ✅ MONEDA
    purchase_items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    # ✅ VENEZUELA: Información fiscal por item
    tax_rate = Column(Float, default=16.0)  # Tasa impositiva (16%, 8%, 0%)
    tax_amount = Column(Float, default=0.0)  # IVA por item
    is_exempt = Column(Boolean, default=False)  # Si el item está exento de IVA

    purchase = relationship("Purchase", back_populates="purchase_items")
    product = relationship("Product", back_populates="purchase_items")

# ✅ MONEDAS (Currency) - Soporte multi-moneda
class Currency(Base):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    code = Column(String(3), nullable=False, unique=True)  # ISO 4217: USD, VES, EUR, etc.
    name = Column(String(50), nullable=False)  # Dólar estadounidense, Bolívar, Euro
    symbol = Column(String(5), nullable=False)  # $, Bs, €
    exchange_rate = Column(Float, default=1.0)  # Tasa de cambio respecto a moneda base
    is_base_currency = Column(Boolean, default=False)  # Si es la moneda base de la empresa
    is_active = Column(Boolean, default=True)

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<Currency {self.code} - {self.name}>"


# ✅ UNIDADES DE MEDIDA (Unit) - Para productos
class Unit(Base):
    __tablename__ = 'units'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    name = Column(String(50), nullable=False)  # Kilogramo, Litro, Unidad
    abbreviation = Column(String(10), nullable=False)  # KG, LTS, UND
    description = Column(String(200))  # Descripción opcional

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<Unit {self.abbreviation} - {self.name}>"


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    username = Column(String(60), nullable=False, index=True)
    email = Column(String(100), index=True)  # ✅ AGREGADO
    hashed_password = Column(String(255))
    
    # Roles y permisos
    role = Column(String(30), default="user")  # admin, manager, user, viewer
    is_active = Column(Boolean, default=True)
    is_company_admin = Column(Boolean, default=False)
    
    # Metadatos
    created_at = Column(DateTime, default=func.now())
    last_login = Column(DateTime)

    # Relaciones
    company = relationship("Company", back_populates="users")

# Funciones de utilidad
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Base de datos falsa para testing (opcional, se puede quitar)
fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": hash_password("secret"),
        "disabled": False,
    }
}