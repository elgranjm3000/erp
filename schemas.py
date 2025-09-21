from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime

# Import para evitar problemas de referencias circulares
if TYPE_CHECKING:
    from .schemas import Product, Category


class CompanyRegistrationRequest(BaseModel):
    # Datos de la compañía
    company_name: str
    company_legal_name: Optional[str] = None  # Si no se proporciona, usar company_name
    company_tax_id: str
    company_address: str
    company_phone: Optional[str] = None
    company_email: Optional[EmailStr] = None
    
    currency: Optional[str] = "USD"
    timezone: Optional[str] = "UTC"
    date_format: Optional[str] = "YYYY-MM-DD"
    invoice_prefix: Optional[str] = "INV"
    
    # Datos del usuario administrador
    admin_username: str
    admin_email: EmailStr
    admin_password: str
    
    @validator('company_tax_id')
    def validate_tax_id(cls, v):
        if len(v) < 3:
            raise ValueError('Tax ID must be at least 3 characters long')
        return v.upper()
    
    @validator('admin_username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens and underscores')
        return v.lower()
    
    @validator('admin_password')
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        return v
    
    @validator('company_name')
    def validate_company_name(cls, v):
        if len(v) < 2:
            raise ValueError('Company name must be at least 2 characters long')
        return v.strip()

class CompanyRegistrationResponse(BaseModel):
    message: str
    company: 'Company'
    admin_user: 'User'
    access_token: str
    token_type: str

# ================= ESQUEMAS DE EMPRESA =================

class CompanyBase(BaseModel):
    name: str
    legal_name: Optional[str] = None
    tax_id: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    currency: str = "USD"
    timezone: str = "UTC"
    invoice_prefix: str = "INV"

class CompanyCreate(CompanyBase):
    # Datos del primer usuario admin
    admin_username: str
    admin_email: EmailStr
    admin_password: str
    
    @validator('tax_id')
    def validate_tax_id(cls, v):
        if len(v) < 5:
            raise ValueError('Tax ID must be at least 5 characters')
        return v.upper()

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    legal_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    logo_url: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    invoice_prefix: Optional[str] = None

class Company(CompanyBase):
    id: int
    logo_url: Optional[str] = None
    next_invoice_number: int
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE USUARIO =================

class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: str = "user"

class UserCreate(UserBase):
    password: str
    company_id: Optional[int] = None  # Para super admin

class UserCreateForCompany(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "user"
    is_company_admin: bool = False

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_company_admin: Optional[bool] = None

class User(UserBase):
    id: int
    company_id: int
    is_active: bool
    is_company_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

class UserWithCompany(User):
    company: Company

# ================= ESQUEMAS DE AUTENTICACIÓN =================

class LoginRequest(BaseModel):
    username: str
    password: str
    company_tax_id: Optional[str] = None  # RIF/NIT de la empresa

class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserWithCompany

class Token(BaseModel):
    access_token: str
    token_type: str

# Esquemas legacy para compatibilidad
class Login(BaseModel):
    username: str
    password: str

# ================= ESQUEMAS DE PRODUCTOS =================

class ProductBase(BaseModel):
    name: str
    description: str
    price: int
    quantity: int
    category_id: int
    sku: Optional[str] = None

class ProductCreate(ProductBase):
    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[int] = None
    quantity: Optional[int] = None
    category_id: Optional[int] = None
    sku: Optional[str] = None

    class Config:
        from_attributes = True

class Product(ProductBase):
    id: int
    company_id: int
    category: Optional["CategoryBase"] = None

    class Config:
        from_attributes = True

class ProductBulkUpdate(BaseModel):
    product_id: int
    price: Optional[int] = None
    quantity: Optional[int] = None

# ================= ESQUEMAS DE CATEGORÍAS =================

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class Category(CategoryBase):
    id: int
    company_id: int
    products: List[ProductBase] = []

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE ALMACENES =================

class WarehouseBase(BaseModel):
    name: str
    location: str

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None

class Warehouse(WarehouseBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE WAREHOUSE-PRODUCTS =================

class WarehouseProductCreate(BaseModel):
    warehouse_id: int
    product_id: int
    stock: int

    @validator('stock')
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

class WarehouseProductUpdate(BaseModel):
    stock: int

    @validator('stock')
    def validate_stock(cls, v):
        if v < 0:
            raise ValueError('Stock cannot be negative')
        return v

class WarehouseProduct(BaseModel):
    warehouse_id: int
    product_id: int
    stock: int

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE CLIENTES =================

class CustomerBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class Customer(CustomerBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE PROVEEDORES =================

class SupplierBase(BaseModel):
    name: str
    contact: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(BaseModel):
    name: Optional[str] = None
    contact: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None

class Supplier(SupplierBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE FACTURAS =================

class InvoiceItemCreate(BaseModel):
    product_id: int
    quantity: int

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class InvoiceItem(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float

    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    customer_id: int
    warehouse_id: int
    status: str = "presupuesto"
    discount: Optional[float] = 0.0
    items: List[InvoiceItemCreate]

    @validator('discount')
    def validate_discount(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Discount must be between 0 and 100')
        return v

class InvoiceUpdate(BaseModel):
    customer_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None
    discount: Optional[float] = None
    items: Optional[List[InvoiceItemCreate]] = None

class Invoice(BaseModel):
    id: int
    company_id: int
    customer_id: int
    warehouse_id: int
    invoice_number: str
    date: datetime
    total_amount: float
    status: str
    discount: float
    items: List[InvoiceItem]

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE COMPRAS =================

class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @validator('price_per_unit')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

class PurchaseItem(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float

    class Config:
        from_attributes = True

class PurchaseCreate(BaseModel):
    supplier_id: int
    warehouse_id: int
    date: datetime
    status: Optional[str] = "pending"
    items: List[PurchaseItemCreate]

class PurchaseUpdate(BaseModel):
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None
    items: Optional[List[PurchaseItemCreate]] = None

class Purchase(BaseModel):
    id: int
    company_id: int
    supplier_id: int
    warehouse_id: int
    purchase_number: str
    date: datetime
    total_amount: float
    status: str
    items: List[PurchaseItem]

    class Config:
        from_attributes = True

class PurchaseResponse(BaseModel):
    id: int
    company_id: int
    supplier_id: int
    warehouse_id: int
    purchase_number: str
    date: datetime
    status: str
    total_amount: float

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE MOVIMIENTOS =================

class InventoryMovementBase(BaseModel):
    product_id: int
    invoice_id: Optional[int] = None
    movement_type: str
    quantity: int

class InventoryMovementCreate(InventoryMovementBase):
    @validator('movement_type')
    def validate_movement_type(cls, v):
        valid_types = ['entrada', 'salida', 'ajuste', 'transferencia']
        if v not in valid_types:
            raise ValueError(f'Movement type must be one of: {valid_types}')
        return v

class InventoryMovement(InventoryMovementBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE REPORTES Y DASHBOARD =================

class CompanyDashboard(BaseModel):
    company: Company
    total_products: int
    total_customers: int
    total_warehouses: int
    monthly_sales: float
    pending_invoices: int
    low_stock_products: int

class CompanySettings(BaseModel):
    currency: str
    timezone: str
    date_format: str
    invoice_prefix: str
    next_invoice_number: int
    low_stock_threshold: int = 10
    auto_increment_invoice: bool = True
    require_customer_tax_id: bool = False

class ProductStats(BaseModel):
    total_products: int
    total_value: float
    low_stock_count: int
    out_of_stock_count: int
    categories_count: int

# ================= ESQUEMAS DE CRÉDITO =================

class CreditMovementCreate(BaseModel):
    invoice_id: int
    amount: float
    movement_type: str  # 'nota_credito', 'devolucion'

    @validator('movement_type')
    def validate_movement_type(cls, v):
        valid_types = ['nota_credito', 'devolucion']
        if v not in valid_types:
            raise ValueError(f'Movement type must be one of: {valid_types}')
        return v

    @validator('amount')
    def validate_amount(cls, v):
        if v <= 0:
            raise ValueError('Amount must be greater than 0')
        return v

class CreditMovement(CreditMovementCreate):
    id: int
    date: datetime

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE RESPUESTA DE ERROR =================

class ErrorResponse(BaseModel):
    error: bool = True
    message: str
    status_code: int
    detail: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool = True
    message: str
    data: Optional[dict] = None