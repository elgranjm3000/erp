from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base
from passlib.context import CryptContext


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# Cliente
class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    phone = Column(String)
    address = Column(String)

    invoices = relationship("Invoice", back_populates="customer")

# Factura
class Invoice(Base):
    __tablename__ = 'invoices'

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey('customers.id'))
    date = Column(DateTime, default=func.now())
    total_amount = Column(Float)
    status = Column(String)  # 'presupuesto', 'factura', 'nota_credito', 'devolucion'
    warehouse_id = Column(Integer)


    customer = relationship("Customer", back_populates="invoices")
    invoice_items = relationship("InvoiceItem", back_populates="invoice")

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
    movement_type = Column(String)  # 'nota_credito' o 'devolucion'
    date = Column(DateTime, default=func.now())

    invoice = relationship("Invoice")

# Categoría de producto
class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)

    products = relationship("Product", back_populates="category")

# Producto
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    price = Column(Integer)
    quantity = Column(Integer, default=0)
    category_id = Column(Integer, ForeignKey('categories.id'))

    category = relationship("Category", back_populates="products")
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    
    # Relación con Warehouse a través de la tabla intermedia 'warehouse_products'
    warehouses = relationship("Warehouse", secondary="warehouse_products", back_populates="products")

# Almacén
class Warehouse(Base):
    __tablename__ = 'warehouses'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    location = Column(String)

    # Relación con Product a través de la tabla intermedia 'warehouse_products'
    products = relationship("Product", secondary="warehouse_products", back_populates="warehouses")

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
    movement_type = Column(String)  # Puede ser 'entrada', 'salida'
    quantity = Column(Integer)
    timestamp = Column(DateTime, default=func.now())

    product = relationship("Product", back_populates="inventory_movements")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)  
    hashed_password = Column(String)  
    disabled = False


def hash_password(password: str) -> str:
    return pwd_context.hash(password)

# Función para verificar la contraseña
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)




fake_users_db = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": hash_password("secret"),  # La contraseña se debe almacenar de forma segura
        "disabled": False,
    }
}