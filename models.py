from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean
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
    timezone = Column(String(50), default="UTC")
    date_format = Column(String(20), default="YYYY-MM-DD")
    
    # Configuraciones de facturación
    invoice_prefix = Column(String(10), default="INV")  # INV, FAC, etc.
    next_invoice_number = Column(Integer, default=1)
    
    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    users = relationship("User", back_populates="company")
    warehouses = relationship("Warehouse", back_populates="company")
    products = relationship("Product", back_populates="company")
    customers = relationship("Customer", back_populates="company")
    suppliers = relationship("Supplier", back_populates="company")  # ✅ CORREGIDO
    invoices = relationship("Invoice", back_populates="company")
    purchases = relationship("Purchase", back_populates="company")

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

    # Relaciones
    invoices = relationship("Invoice", back_populates="customer")
    company = relationship("Company", back_populates="customers")

# Factura
class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'))  # ✅ CORREGIDO: FK explícita
    
    # Numeración por empresa
    invoice_number = Column(String(20), index=True)  # ✅ AGREGADO
    
    date = Column(DateTime, default=func.now())
    total_amount = Column(Float)
    status = Column(String(60))  # 'presupuesto', 'factura', 'nota_credito', 'devolucion'
    discount = Column(Float, default=0.0)

    # Relaciones
    customer = relationship("Customer", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")
    company = relationship("Company", back_populates="invoices")
    warehouse = relationship("Warehouse")  # ✅ AGREGADO

# Detalle de la Factura
class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    total_price = Column(Float)

    invoice = relationship("Invoice", back_populates="invoice_items")
    product = relationship("Product")

# Movimiento de Crédito (para notas de crédito y devoluciones)
class CreditMovement(Base):
    __tablename__ = 'credit_movements'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    amount = Column(Float)
    movement_type = Column(String(60))  # 'nota_credito' o 'devolucion'
    date = Column(DateTime, default=func.now())

    invoice = relationship("Invoice")

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
    invoice_id = Column(Integer)
    movement_type = Column(String(60))  # Puede ser 'entrada', 'salida'
    quantity = Column(Integer)
    timestamp = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="inventory_movements")

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
    
    date = Column(DateTime, default=func.now())
    total_amount = Column(Float, default=0.0)
    status = Column(String(60), default="pending")

    # Relaciones
    company = relationship("Company", back_populates="purchases")
    supplier = relationship("Supplier", back_populates="purchases")
    warehouse = relationship("Warehouse", back_populates="purchases")
    purchase_items = relationship("PurchaseItem", back_populates="purchase", cascade="all, delete")

class PurchaseItem(Base):
    __tablename__ = "purchase_items"

    id = Column(Integer, primary_key=True, index=True)
    purchase_id = Column(Integer, ForeignKey("purchases.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_per_unit = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)

    purchase = relationship("Purchase", back_populates="purchase_items")
    product = relationship("Product", back_populates="purchase_items")

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