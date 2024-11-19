from pydantic import BaseModel
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

# Import para evitar problemas de referencias circulares
if TYPE_CHECKING:
    from .schemas import Product, Category

# Esquema para el producto (sin categoría completa)
class ProductBase(BaseModel):
    name: str
    description: str
    price: int
    quantity: int
    category_id: int

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    quantity: Optional[int] = None
    category_id: Optional[int] = None

    class Config:
        from_attributes = True


# Esquema para crear o actualizar una relación warehouse-product
class WarehouseProductCreate(BaseModel):
    warehouse_id: int
    product_id: int
    stock: int

# Esquema para actualizar solo el stock
class WarehouseProductUpdate(BaseModel):
    stock: int

# Esquema para devolver un warehouse-product
class WarehouseProduct(BaseModel):
    warehouse_id: int
    product_id: int
    stock: int

    class Config:
        from_attributes = True

# Producto con referencia simple a la categoría
class Product(ProductBase):
    id: int
    category: Optional["CategoryBase"] = None  # Cambiar a CategoryBase para evitar ciclos

    class Config:
        from_attributes = True

# Esquema para la categoría (sin productos completos)
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

# Categoría con productos sin la referencia completa a la categoría
class Category(CategoryBase):
    id: int
    products: List[ProductBase] = []  # Cambiar a ProductBase para evitar ciclos

    class Config:
        from_attributes = True

# Esquema para el movimiento de inventario
class InventoryMovementBase(BaseModel):
    product_id: int
    invoice_id: Optional[int]
    movement_type: str
    quantity: int

class InventoryMovementCreate(InventoryMovementBase):
    pass

class InventoryMovement(InventoryMovementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# Esquema para almacén
class WarehouseBase(BaseModel):
    name: str
    location: str

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    id: int

    class Config:
        from_attributes = True

# Esquema para la creación de usuarios (si es necesario)
class UserCreate(BaseModel):
    username: str
    password: str

# Esquema para el login
class Login(BaseModel):
    username: str
    password: str

# Esquema para el token de acceso
class Token(BaseModel):
    access_token: str
    token_type: str

class CreditMovementCreate(BaseModel):
    invoice_id: int
    amount: float
    movement_type: str  # 'nota_credito', 'devolucion'

class InvoiceItem(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float

    class Config:
        from_attributes = True

class Invoice(BaseModel):
    customer_id: int
    warehouse_id: int
    status: str  # 'presupuesto', 'factura', etc.
    date: datetime
    total_amount: float
    discount: Optional[float] = 0.0  # Nuevo campo de descuento
    items: List[InvoiceItem]   


    class Config:
        from_attributes = True

class PurchaseItemBase(BaseModel):
    quantity: int
    price_per_unit: float

class PurchaseItemCreate(PurchaseItemBase):
    pass

class PurchaseItem(PurchaseItemBase):
    product_id: int
    class Config:
        from_attributes = True

class PurchaseBase(BaseModel):
    supplier_id: int
    warehouse_id: int
    date: datetime
    status: Optional[str] = "pending"

class PurchaseCreate(PurchaseBase):
    items: List[PurchaseItemCreate]

class Purchase(PurchaseBase):

    supplier_id:int 
    warehouse_id:int                                
    date: datetime
    total_amount: float
    items: List[PurchaseItem]

    class Config:
        from_attributes = True

class PurchaseResponse(BaseModel):
    id: int
    supplier_id: int
    warehouse_id: int
    date: datetime
    status: Optional[str] = "pending"
    total_amount: float

    class Config:
        from_attributes = True
