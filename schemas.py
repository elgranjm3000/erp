from pydantic import BaseModel, EmailStr, validator
from typing import List, Optional, TYPE_CHECKING, Union
from datetime import datetime, date, time

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
    exchange_rate: Optional[float] = None  # ✅ VENEZUELA: Tasa de cambio USD->VES
    timezone: str = "UTC"
    invoice_prefix: str = "INV"
    require_customer_tax_id_threshold: Optional[float] = None  # ✅ VENEZUELA: Monto mínimo para requerir RIF

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
    exchange_rate: Optional[float] = None  # ✅ VENEZUELA: Tasa de cambio USD->VES
    timezone: Optional[str] = None
    invoice_prefix: Optional[str] = None
    require_customer_tax_id_threshold: Optional[float] = None  # ✅ VENEZUELA: Monto mínimo para requerir RIF

    # ✅ VENEZUELA: Agentes de retención
    iva_retention_agent: Optional[bool] = None
    islr_retention_agent: Optional[bool] = None

class Company(CompanyBase):
    id: int
    logo_url: Optional[str] = None
    next_invoice_number: int
    created_at: datetime
    is_active: bool

    # ✅ VENEZUELA: Agentes de retención
    iva_retention_agent: bool = False
    islr_retention_agent: bool = False

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
    # ✅ Campos básicos
    name: str
    short_name: Optional[str] = None  # ✅ SISTEMA ESCRITORIO
    description: Optional[str] = None
    sku: Optional[str] = None

    # ✅ SISTEMA ESCRITORIO: Clasificación
    mark: Optional[str] = None  # Marca
    model: Optional[str] = None  # Modelo
    department_id: Optional[int] = None  # Departamento
    size: Optional[str] = None  # Talla
    color: Optional[str] = None  # Color
    product_type: str = 'T'  # T=Terminado, S=Servicio, C=Compuesto

    # ✅ SISTEMA ESCRITORIO: Impuestos (códigos)
    sale_tax_code: str = '01'  # 01=16%, 02=31%, 03=8%, 06=Percibido, EX=Exento
    buy_tax_code: str = '01'

    # ✅ Precios (múltiples niveles)
    price: Optional[float] = None  # Legacy - Precio local (VES)
    price_usd: Optional[float] = None  # Precio referencial en USD
    cost: Optional[float] = None  # Costo del producto
    maximum_price: Optional[float] = None  # ✅ Precio máximo
    offer_price: Optional[float] = None  # ✅ Precio oferta
    higher_price: Optional[float] = None  # ✅ Precio mayor
    minimum_price: Optional[float] = None  # ✅ Precio mínimo
    sale_price_type: int = 0  # ✅ 0=Max, 1=Oferta, 2=Mayor, 3=Min, 4=Variable

    # ✅ Stock e inventario
    quantity: Optional[int] = None  # Stock actual
    stock_quantity: Optional[int] = None  # ✅ Stock actual (alternativo)
    minimal_stock: Optional[int] = None  # ✅ Stock mínimo
    maximum_stock: Optional[int] = None  # ✅ Stock máximo
    allow_negative_stock: bool = False  # ✅ Permitir vender sin stock
    serialized: bool = False  # ✅ Usa serial
    use_lots: bool = False  # ✅ Usa lotes
    lots_order: int = 0  # ✅ 0=PEPS, 1=PUPS, 2=Vencimiento

    # ✅ Costeo
    costing_type: int = 0  # ✅ 0=Promedio, 1=Último, 2=PEPS, 3=UEPS
    calculated_cost: Optional[float] = None  # ✅ Costo calculado
    average_cost: Optional[float] = None  # ✅ Costo promedio

    # ✅ Descuentos y límites de venta
    discount: float = 0  # ✅ Descuento del producto
    max_discount: float = 0  # ✅ Máximo descuento permitido
    minimal_sale: float = 0  # ✅ Cantidad mínima de venta
    maximal_sale: float = 0  # ✅ Cantidad máxima de venta

    # ✅ Configuraciones adicionales
    allow_decimal: bool = True  # ✅ Permitir decimales en cantidad
    rounding_type: int = 2  # ✅ Decimales: 0=0,0, 2=0,00, 4=0,0000
    edit_name: bool = False  # ✅ Permitir editar nombre en ventas
    take_department_utility: bool = True  # ✅ Usar utilidad del departamento

    # ✅ Moneda
    coin: str = '01'  # ✅ 01=Bolívar, 02=Dólar

    # ✅ Garantía
    days_warranty: int = 0  # ✅ Días de garantía

    # ✅ Estado
    status: str = '01'  # ✅ 01=Activo, 02=Inactivo

    # ✅ Campos legacy (compatibilidad)
    category_id: Optional[int] = None
    currency_id: Optional[int] = None
    warehouse_id: Optional[int] = None  # ✅ Depósito/Almacén del producto


class ProductCreate(ProductBase):
    @validator('price')
    def validate_price(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Price must be greater than 0')
        return v

    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 0:
            raise ValueError('Quantity cannot be negative')
        return v


class ProductUpdate(BaseModel):
    # ✅ Todos los campos opcionales para actualización parcial
    name: Optional[str] = None
    short_name: Optional[str] = None
    description: Optional[str] = None
    sku: Optional[str] = None
    mark: Optional[str] = None
    model: Optional[str] = None
    department_id: Optional[int] = None
    size: Optional[str] = None
    color: Optional[str] = None
    product_type: Optional[str] = None
    sale_tax_code: Optional[str] = None
    buy_tax_code: Optional[str] = None
    price: Optional[float] = None
    price_usd: Optional[float] = None
    cost: Optional[float] = None
    maximum_price: Optional[float] = None
    offer_price: Optional[float] = None
    higher_price: Optional[float] = None
    minimum_price: Optional[float] = None
    sale_price_type: Optional[int] = None
    quantity: Optional[int] = None
    stock_quantity: Optional[int] = None
    minimal_stock: Optional[int] = None
    maximum_stock: Optional[int] = None
    allow_negative_stock: Optional[bool] = None
    serialized: Optional[bool] = None
    use_lots: Optional[bool] = None
    lots_order: Optional[int] = None
    costing_type: Optional[int] = None
    calculated_cost: Optional[float] = None
    average_cost: Optional[float] = None
    discount: Optional[float] = None
    max_discount: Optional[float] = None
    minimal_sale: Optional[float] = None
    maximal_sale: Optional[float] = None
    allow_decimal: Optional[bool] = None
    rounding_type: Optional[int] = None
    edit_name: Optional[bool] = None
    take_department_utility: Optional[bool] = None
    coin: Optional[str] = None
    days_warranty: Optional[int] = None
    status: Optional[str] = None
    category_id: Optional[int] = None
    currency_id: Optional[int] = None
    warehouse_id: Optional[int] = None  # ✅ Depósito/Almacén del producto

    class Config:
        from_attributes = True


class WarehouseStockInfo(BaseModel):
    """Información de stock en un almacén"""
    warehouse_id: int
    warehouse_name: str
    warehouse_location: str
    stock: int

    class Config:
        from_attributes = True


class Product(ProductBase):
    id: int
    company_id: int
    category: Optional["CategoryBase"] = None
    department: Optional["DepartmentBase"] = None  # ✅ SISTEMA ESCRITORIO
    warehouse: Optional["WarehouseBase"] = None  # ✅ Depósito/Almacén del producto

    class Config:
        from_attributes = True


class ProductWithWarehouses(ProductBase):
    """Producto con información de stock en todos los almacenes"""
    id: int
    company_id: int
    category: Optional["CategoryBase"] = None
    department: Optional["DepartmentBase"] = None  # ✅ SISTEMA ESCRITORIO
    warehouse: Optional["WarehouseBase"] = None  # ✅ Depósito/Almacén principal del producto
    warehouses: List[WarehouseStockInfo] = []

    class Config:
        from_attributes = True


class ProductBulkUpdate(BaseModel):
    product_id: int
    price: Optional[float] = None
    price_usd: Optional[float] = None
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

class WarehouseProductWithDetails(BaseModel):
    """Esquema para productos de almacén con información completa del producto"""
    product_id: int
    warehouse_id: int
    stock: int
    product_name: str
    product_description: Optional[str] = None
    product_sku: Optional[str] = None
    product_price: float

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE CLIENTES =================

class CustomerBase(BaseModel):
    # ✅ Campos básicos
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None  # ✅ VENEZUELA: RIF/CI del cliente
    latitude: Optional[float] = None  # ✅ UBICACIÓN: Latitud para mapa
    longitude: Optional[float] = None  # ✅ UBICACIÓN: Longitud para mapa
    contact_name: Optional[str] = None  # ✅ SISTEMA ESCRITORIO: Nombre del contacto

    # ✅ SISTEMA ESCRITORIO: Clasificación fiscal
    name_fiscal: int = 1  # ✅ 0=Ordinario, 1=No Contribuyente, 2=Formal
    client_type: str = '01'  # ✅ 01=Juridico, 02=Natural, 03=Government

    # ✅ SISTEMA ESCRITORIO: Retenciones
    retention_tax_agent: bool = False  # ✅ Agente de retención IVA
    retention_municipal_agent: bool = False  # ✅ Agente de retención municipal
    retention_islr_agent: bool = False  # ✅ Agente de retención ISLR

    # ✅ SISTEMA ESCRITORIO: Crédito
    credit_days: int = 0  # ✅ Días de crédito
    credit_limit: float = 0  # ✅ Límite de crédito
    allow_expired_balance: bool = False  # ✅ Permitir vender con saldo vencido

    # ✅ SISTEMA ESCRITORIO: Asignaciones
    seller_id: Optional[int] = None  # ✅ Vendedor asignado
    client_group_id: Optional[int] = None  # ✅ Grupo de cliente
    area_sales_id: Optional[int] = None  # ✅ Área de ventas

    # ✅ SISTEMA ESCRITORIO: Precios y descuentos
    sale_price: int = 1  # ✅ 0=Max, 1=Oferta, 2=Mayor, 3=Min, 4=Variable
    discount: float = 0  # ✅ Descuento fijo del cliente

    # ✅ SISTEMA ESCRITORIO: Estado
    status: str = '01'  # ✅ 01=Activo, 02=Inactivo

    @validator('tax_id')
    def validate_tax_id(cls, v):
        if v and len(v) > 0:
            # Solo validar longitud máxima, mínima puede ser 1 para compatibilidad
            if len(v) > 20:
                raise ValueError('Tax ID must be maximum 20 characters')
            return v.upper() if v else v
        return v

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None:
            if not -90 <= v <= 90:
                raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None:
            if not -180 <= v <= 180:
                raise ValueError('Longitude must be between -180 and 180')
        return v

    @validator('name_fiscal')
    def validate_name_fiscal(cls, v):
        if v not in [0, 1, 2]:
            raise ValueError('name_fiscal must be 0 (Ordinario), 1 (No Contribuyente), or 2 (Formal)')
        return v

    @validator('client_type')
    def validate_client_type(cls, v):
        if v not in ['01', '02', '03']:
            raise ValueError('client_type must be 01 (Juridico), 02 (Natural), or 03 (Government)')
        return v

    @validator('status')
    def validate_status(cls, v):
        if v not in ['01', '02']:
            raise ValueError('status must be 01 (Active) or 02 (Inactive)')
        return v


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    # ✅ Todos los campos opcionales para actualización parcial
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    tax_id: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    contact_name: Optional[str] = None
    name_fiscal: Optional[int] = None
    client_type: Optional[str] = None
    retention_tax_agent: Optional[bool] = None
    retention_municipal_agent: Optional[bool] = None
    retention_islr_agent: Optional[bool] = None
    credit_days: Optional[int] = None
    credit_limit: Optional[float] = None
    allow_expired_balance: Optional[bool] = None
    seller_id: Optional[int] = None
    client_group_id: Optional[int] = None
    area_sales_id: Optional[int] = None
    sale_price: Optional[int] = None
    discount: Optional[float] = None
    status: Optional[str] = None

    @validator('latitude')
    def validate_latitude(cls, v):
        if v is not None:
            if not -90 <= v <= 90:
                raise ValueError('Latitude must be between -90 and 90')
        return v

    @validator('longitude')
    def validate_longitude(cls, v):
        if v is not None:
            if not -180 <= v <= 180:
                raise ValueError('Longitude must be between -180 and 180')
        return v


class Customer(CustomerBase):
    id: int
    company_id: int
    seller: Optional["SellerBase"] = None  # ✅ SISTEMA ESCRITORIO
    client_group: Optional["ClientGroupBase"] = None  # ✅ SISTEMA ESCRITORIO
    area_sales: Optional["AreasSalesBase"] = None  # ✅ SISTEMA ESCRITORIO

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
    tax_rate: Optional[float] = 16.0  # ✅ VENEZUELA: Tasa de IVA (16%, 8%, 0%)
    is_exempt: Optional[bool] = False  # ✅ VENEZUELA: Si está exento de IVA

    # ✅ MONEDA: Cada item puede tener su propia moneda
    currency_id: Optional[int] = None  # Si es null, usa moneda de la factura
    price_per_unit: Optional[float] = None  # Si es null, usa precio del producto

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

    @validator('tax_rate')
    def validate_tax_rate(cls, v):
        if v is not None and v not in [0, 8, 16]:
            raise ValueError('Tax rate must be 0%%, 8%%, or 16%%')
        return v

class InvoiceItem(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float
    tax_rate: Optional[float] = 16.0  # ✅ VENEZUELA
    tax_amount: Optional[float] = 0.0  # ✅ VENEZUELA
    is_exempt: Optional[bool] = False  # ✅ VENEZUELA

    # ✅ MONEDA: Información de moneda del item
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[datetime] = None
    base_currency_amount: Optional[float] = 0.0

    # ✅ INCLUDE PRODUCT DETAILS
    product_name: Optional[str] = None
    product_description: Optional[str] = None
    product_sku: Optional[str] = None

    class Config:
        from_attributes = True

class InvoiceCreate(BaseModel):
    customer_id: int
    warehouse_id: int
    status: str = "factura"
    discount: Optional[float] = 0.0
    date: date
    items: List[InvoiceItemCreate]
    notes: Optional[str] = None
    payment_terms: Optional[str] = None

    # ✅ MONEDA: Moneda de la factura
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None  # Tasa de cambio histórica
    exchange_rate_date: Optional[datetime] = None  # Fecha de la tasa de cambio

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = "contado"  # 'contado', 'credito'
    payment_method: Optional[str] = "efectivo"  # 'efectivo', 'transferencia', etc.
    credit_days: Optional[int] = 0
    iva_percentage: Optional[float] = 16.0  # 16%, 8%, 0%
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    # ✅ IGTF: Configuración opcional
    igtf_exempt: Optional[bool] = False  # Forzar exención IGTF

    @validator('discount')
    def validate_discount(cls, v):
        if v is not None and (v < 0 or v > 100):
            raise ValueError('Discount must be between 0 and 100')
        return v

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v not in ['contado', 'credito']:
            raise ValueError('Transaction type must be "contado" or "credito"')
        return v

    @validator('iva_percentage')
    def validate_iva_percentage(cls, v):
        if v is not None and v not in [0, 8, 16]:
            raise ValueError('IVA percentage must be 0%%, 8%%, or 16%%')
        return v

    class Config:
        from_attributes = True

class InvoiceUpdate(BaseModel):
    customer_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None
    discount: Optional[float] = None
    items: Optional[List[InvoiceItemCreate]] = None
    notes: Optional[str] = None
    payment_terms: Optional[str] = None

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = None
    payment_method: Optional[str] = None
    credit_days: Optional[int] = None
    iva_percentage: Optional[float] = None
    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    class Config:
        from_attributes = True

class Invoice(BaseModel):
    id: int
    company_id: int
    customer_id: int
    warehouse_id: int
    invoice_number: str
    control_number: Optional[str] = None  # ✅ VENEZUELA
    date: date
    total_amount: float
    status: str
    discount: float
    notes: Optional[str] = None

    # ✅ MONEDA: Información de moneda
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[datetime] = None
    reference_currency_id: Optional[int] = None  # ✅ SISTEMA REF: Moneda de referencia (USD)

    # ✅ SISTEMA REF: Precios de referencia
    subtotal_reference: Optional[float] = None  # Subtotal en moneda de referencia (USD)
    subtotal_target: Optional[float] = None  # Subtotal en moneda de pago (VES)

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = "contado"
    payment_method: Optional[str] = None
    credit_days: Optional[int] = 0
    iva_percentage: Optional[float] = 16.0
    iva_amount: Optional[float] = 0.0
    taxable_base: Optional[float] = 0.0
    exempt_amount: Optional[float] = 0.0
    iva_retention: Optional[float] = 0.0
    iva_retention_percentage: Optional[float] = 0.0
    islr_retention: Optional[float] = 0.0
    islr_retention_percentage: Optional[float] = 0.0
    stamp_tax: Optional[float] = 0.0
    subtotal: Optional[float] = 0.0
    total_with_taxes: Optional[float] = 0.0

    # ✅ IGTF: Campos de IGTF
    igtf_amount: Optional[float] = 0.0
    igtf_percentage: Optional[float] = 0.0
    igtf_exempt: Optional[bool] = False

    customer_phone: Optional[str] = None
    customer_address: Optional[str] = None

    items: List[InvoiceItem] = []

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE COMPRAS =================

class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    tax_rate: Optional[float] = 16.0  # ✅ VENEZUELA: Tasa de IVA
    is_exempt: Optional[bool] = False  # ✅ VENEZUELA: Si está exento de IVA

    # ✅ MONEDA: Cada item puede tener su propia moneda
    currency_id: Optional[int] = None  # Si es null, usa moneda de la compra

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

    @validator('tax_rate')
    def validate_tax_rate(cls, v):
        if v is not None and v not in [0, 8, 16]:
            raise ValueError('Tax rate must be 0%%, 8%%, or 16%%')
        return v

class PurchaseItem(BaseModel):
    product_id: int
    quantity: int
    price_per_unit: float
    total_price: float
    tax_rate: Optional[float] = 16.0  # ✅ VENEZUELA
    tax_amount: Optional[float] = 0.0  # ✅ VENEZUELA
    is_exempt: Optional[bool] = False  # ✅ VENEZUELA

    # ✅ MONEDA: Información de moneda del item
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[datetime] = None
    base_currency_amount: Optional[float] = 0.0

    class Config:
        from_attributes = True

class PurchaseCreate(BaseModel):
    supplier_id: int
    warehouse_id: int
    date: datetime
    status: Optional[str] = "pending"
    items: List[PurchaseItemCreate]

    # ✅ MONEDA: Moneda de la compra
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None  # Tasa de cambio histórica
    exchange_rate_date: Optional[datetime] = None  # Fecha de la tasa de cambio

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = "contado"  # 'contado', 'credito'
    payment_method: Optional[str] = "efectivo"  # 'efectivo', 'transferencia', etc.
    credit_days: Optional[int] = 0
    iva_percentage: Optional[float] = 16.0  # 16%, 8%, 0%
    invoice_number: Optional[str] = None  # ✅ Número de factura del proveedor
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None

    @validator('transaction_type')
    def validate_transaction_type(cls, v):
        if v not in ['contado', 'credito']:
            raise ValueError('Transaction type must be "contado" or "credito"')
        return v

    @validator('iva_percentage')
    def validate_iva_percentage(cls, v):
        if v is not None and v not in [0, 8, 16]:
            raise ValueError('IVA percentage must be 0%%, 8%%, or 16%%')
        return v

class PurchaseUpdate(BaseModel):
    supplier_id: Optional[int] = None
    warehouse_id: Optional[int] = None
    status: Optional[str] = None
    items: Optional[List[PurchaseItemCreate]] = None

    # ✅ MONEDA: Moneda de la compra
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = None
    payment_method: Optional[str] = None
    credit_days: Optional[int] = None
    iva_percentage: Optional[float] = None
    invoice_number: Optional[str] = None
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None

class Purchase(BaseModel):
    id: int
    company_id: int
    supplier_id: int
    warehouse_id: int
    purchase_number: str
    invoice_number: Optional[str] = None  # ✅ VENEZUELA
    control_number: Optional[str] = None  # ✅ VENEZUELA
    date: datetime
    total_amount: float
    status: str
    items: List[PurchaseItem]

    # ✅ MONEDA: Información de moneda
    currency_id: Optional[int] = None
    exchange_rate: Optional[float] = None
    exchange_rate_date: Optional[datetime] = None

    # ✅ VENEZUELA: Información fiscal
    transaction_type: Optional[str] = "contado"
    payment_method: Optional[str] = None
    credit_days: Optional[int] = 0
    iva_percentage: Optional[float] = 16.0
    iva_amount: Optional[float] = 0.0
    taxable_base: Optional[float] = 0.0
    exempt_amount: Optional[float] = 0.0
    iva_retention: Optional[float] = 0.0
    iva_retention_percentage: Optional[float] = 0.0
    islr_retention: Optional[float] = 0.0
    islr_retention_percentage: Optional[float] = 0.0
    stamp_tax: Optional[float] = 0.0
    subtotal: Optional[float] = 0.0
    total_with_taxes: Optional[float] = 0.0
    supplier_phone: Optional[str] = None
    supplier_address: Optional[str] = None

    class Config:
        from_attributes = True

class PurchaseResponse(BaseModel):
    id: int
    company_id: int
    supplier_id: int
    warehouse_id: int
    purchase_number: str
    invoice_number: Optional[str] = None  # ✅ VENEZUELA
    control_number: Optional[str] = None  # ✅ VENEZUELA
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
    reason: Optional[str] = None  # ✅ Motivo de la nota de crédito

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

# ================= ESQUEMAS DE CRÉDITO DE COMPRAS =================

class PurchaseCreditMovementCreate(BaseModel):
    purchase_id: int
    amount: float
    movement_type: str  # 'nota_credito', 'devolucion'
    reason: str  # Motivo de la nota de crédito (obligatorio para compras)
    reference_purchase_number: Optional[str] = None  # ✅ Referencia a compra original
    reference_control_number: Optional[str] = None  # ✅ Número de control original
    warehouse_id: Optional[int] = None  # Almacén para revertir stock

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

    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason is required for purchase credit notes')
        return v.strip()

class PurchaseCreditMovement(PurchaseCreditMovementCreate):
    id: int
    date: datetime
    stock_reverted: bool = False

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE TRANSFERENCIA Y AJUSTE DE STOCK =================

class StockTransferCreate(BaseModel):
    from_warehouse_id: int
    to_warehouse_id: int
    product_id: int
    quantity: int

    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be greater than 0')
        return v

class StockAdjustmentCreate(BaseModel):
    warehouse_id: int
    product_id: int
    adjustment: int
    reason: str

    @validator('adjustment')
    def validate_adjustment(cls, v):
        if v == 0:
            raise ValueError('Adjustment cannot be zero')
        return v

    @validator('reason')
    def validate_reason(cls, v):
        if not v or not v.strip():
            raise ValueError('Reason is required')
        return v

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

# ================= ESQUEMAS DE MONEDAS =================

class CurrencyCreate(BaseModel):
    code: str  # ISO 4217: USD, VES, EUR
    name: str  # Dólar estadounidense, Bolívar, Euro
    symbol: str  # $, Bs, €
    exchange_rate: float = 1.0
    is_base_currency: bool = False

    @validator("code")
    def validate_code(cls, v):
        if len(v) != 3:
            raise ValueError("Currency code must be 3 characters (ISO 4217)")
        return v.upper()

    @validator("exchange_rate")
    def validate_exchange_rate(cls, v):
        if v <= 0:
            raise ValueError("Exchange rate must be greater than 0")
        return v

class CurrencyUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    exchange_rate: Optional[float] = None
    is_base_currency: Optional[bool] = None
    is_active: Optional[bool] = None

class Currency(CurrencyCreate):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# ================= ESQUEMAS DE UNIDADES DE MEDIDA =================

class UnitCreate(BaseModel):
    name: str  # Kilogramo, Litro, Unidad
    abbreviation: str  # KG, LTS, UND
    description: Optional[str] = None

    @validator("abbreviation")
    def validate_abbreviation(cls, v):
        if not v or len(v) > 10:
            raise ValueError("Abbreviation must be 1-10 characters")
        return v.upper()

class UnitUpdate(BaseModel):
    name: Optional[str] = None
    abbreviation: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Unit(UnitCreate):
    id: int
    company_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ================= ESQUEMAS DE HISTORIAL DE TASAS DE CAMBIO =================

class ExchangeRateHistoryCreate(BaseModel):
    from_currency_id: int
    to_currency_id: int
    rate: float
    recorded_at: Optional[datetime] = None

    @validator('rate')
    def validate_rate(cls, v):
        if v <= 0:
            raise ValueError('Exchange rate must be greater than 0')
        return v


class ExchangeRateHistory(BaseModel):
    id: int
    company_id: int
    from_currency_id: int
    to_currency_id: int
    rate: float
    recorded_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Historial de monedas (CoinHistory)
class CoinHistoryBase(BaseModel):
    currency_id: int
    sales_aliquot: float  # Tasa de venta
    buy_aliquot: float  # Tasa de compra
    register_date: date  # Fecha del registro
    register_hour: time  # Hora del registro
    user_id: Optional[int] = None  # Usuario que registró


class CoinHistoryCreate(CoinHistoryBase):
    pass


class CoinHistoryUpdate(BaseModel):
    sales_aliquot: Optional[float] = None
    buy_aliquot: Optional[float] = None
    register_date: Optional[date] = None
    register_hour: Optional[time] = None
    user_id: Optional[int] = None

    class Config:
        from_attributes = True


class CoinHistory(CoinHistoryBase):
    id: int
    company_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Monedas (Coins) - Compatible con Desktop ERP
class CoinBase(BaseModel):
    code: str  # Código ISO: USD, VES, EUR
    name: str  # Nombre completo: "Dólar Americano"
    symbol: str  # Símbolo: "$", "Bs"
    exchange_rate: float  # Tasa actual
    factor_type: int = 0  # 0=Moneda base, 1=Moneda convertida
    rounding_type: int = 2  # 0=Sin redondeo, 1=Arriba, 2=Estándar
    status: str = "01"  # Código de estado: "01"=Activo
    show_in_browsers: bool = True  # Mostrar en listados
    value_inventory: bool = False  # Usar para valorar inventario
    applies_igtf: bool = False  # Aplica IGTF


class CoinCreate(CoinBase):
    decimal_places: int = 2
    igtf_rate: Optional[float] = 3.0  # Tasa de IGTF (default 3%)


class CoinUpdate(BaseModel):
    name: Optional[str] = None
    symbol: Optional[str] = None
    exchange_rate: Optional[float] = None
    factor_type: Optional[int] = None
    rounding_type: Optional[int] = None
    status: Optional[str] = None
    show_in_browsers: Optional[bool] = None
    value_inventory: Optional[bool] = None
    applies_igtf: Optional[bool] = None
    decimal_places: Optional[int] = None
    igtf_rate: Optional[float] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class Coin(CoinBase):
    id: int
    company_id: int
    decimal_places: int
    igtf_rate: Optional[float] = None
    is_base_currency: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ================= ESQUEMAS DE PRECIOS DE PRODUCTOS =================

class ProductPriceCreate(BaseModel):
    currency_id: int
    price: float
    is_base_price: bool = False

    @validator('price')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be greater than 0')
        return v


class ProductPriceUpdate(BaseModel):
    price: Optional[float] = None
    is_base_price: Optional[bool] = None


class ProductPrice(ProductPriceCreate):
    id: int
    product_id: int
    updated_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class ProductWithPrices(Product):
    """Producto con todos sus precios en diferentes monedas"""
    prices: List[ProductPrice] = []


class ProductPriceSyncRequest(BaseModel):
    """Request para sincronizar precios de un producto a todas las monedas"""
    base_price: float
    base_currency_id: int

"""
Schemas Pydantic - Configuración de Monedas con Lógica Venezolana
Validación ISO 4217, factores de conversión y cumplimiento tributario
"""

from pydantic import BaseModel, Field, validator, root_validator
from typing import Optional, List, Literal
from datetime import datetime
from decimal import Decimal
from enum import Enum

# Lista oficial de códigos ISO 4217 (actualizada 2024)
ISO_4217_CURRENCIES = {
    # Principales monedas
    "USD": "United States Dollar",
    "EUR": "Euro",
    "GBP": "Pound Sterling",
    "JPY": "Japanese Yen",
    "CNY": "Chinese Yuan",
    "VES": "Venezuelan Bolívar",
    "COP": "Colombian Peso",
    "BRL": "Brazilian Real",
    "MXN": "Mexican Peso",
    "ARS": "Argentine Peso",
    "PEN": "Peruvian Sol",
    "CLP": "Chilean Peso",
    "COP": "Colombian Peso",
    "CAD": "Canadian Dollar",
    "AUD": "Australian Dollar",
    "CHF": "Swiss Franc",
    "TRY": "Turkish Lira",
    "RUB": "Russian Ruble",
    "INR": "Indian Rupee",
    "KRW": "South Korean Won",
    "SGD": "Singapore Dollar",
    "HKD": "Hong Kong Dollar",
    "NOK": "Norwegian Krone",
    "SEK": "Swedish Krona",
    "NZD": "New Zealand Dollar",
    "ZAR": "South African Rand",
    # Criptomonedas (no oficiales ISO pero usadas)
    "USDT": "Tether",
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    # Monedas del Caribe
    "XCD": "East Caribbean Dollar",
    "JMD": "Jamaican Dollar",
    "TTD": "Trinidad and Tobago Dollar",
    "BBD": "Barbadian Dollar",
    "BSD": "Bahamian Dollar",
}


def validate_currency_code(v: str) -> str:
    """Validador de códigos ISO 4217"""
    if not isinstance(v, str):
        raise TypeError('string required')

    v = v.upper().strip()

    if len(v) != 3:
        raise ValueError(
            f"Código de moneda debe tener 3 caracteres (ISO 4217), got: {v}"
        )

    if v not in ISO_4217_CURRENCIES:
        # Warning pero permitimos monedas personalizadas
        import warnings
        warnings.warn(
            f"Código '{v}' no está en lista oficial ISO 4217. "
            f"Usando moneda personalizada.",
            UserWarning
        )

    return v


class ConversionMethod(str, Enum):
    """Métodos de conversión según tipo de moneda"""
    DIRECT = "direct"  # VES -> moneda (moneda más fuerte)
    INVERSE = "inverse"  # moneda -> VES (moneda más débil)
    VIA_USD = "via_usd"  # moneda -> USD -> VES (triangulación)
    UNDEFINED = "undefined"  # VES (moneda base, no aplica)


class RateUpdateMethod(str, Enum):
    """Métodos de actualización de tasas"""
    MANUAL = "manual"
    API_BCV = "api_bcv"
    API_BINANCE = "api_binance"
    API_FIXER = "api_fixer"
    SCRAPER = "scraper"
    SCHEDULED = "scheduled"
    WEBHOOK = "webhook"


class CurrencyCreate(BaseModel):
    """
    Schema para crear una nueva moneda.

    Incluye validación ISO 4217 y lógica de factores de conversión.

    Validadores flexibles que aceptan:
    - exchange_rate: string ("36.5"), float (36.5), o number
    - igtf_rate: string, float o number
    - igtf_min_amount: string, float o number (opcional)
    """

    # Identificación obligatoria
    code: str = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Código ISO 4217 de 3 letras (ej: USD, VES, EUR)"
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Nombre completo de la moneda"
    )

    symbol: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Símbolo para impresión (ej: $, Bs, €)"
    )

    # Configuración de tasa - Acepta string, float, int
    exchange_rate: Union[str, float, int] = Field(
        ...,
        description="Tasa de cambio actual (acepta: '36.5', 36.5, 36.5000000000)"
    )

    decimal_places: int = Field(
        2,
        ge=0,
        le=10,
        description="Decimales para display (default: 2, máx: 10)"
    )

    # Moneda base
    is_base_currency: bool = Field(
        False,
        description="Solo una moneda base por empresa"
    )

    # === FACTOR DE CONVERSIÓN (Lógica venezolana) ===

    conversion_method: Optional[ConversionMethod] = Field(
        None,
        description="""
        Método de conversión:
        - direct: VES -> moneda (moneda más fuerte)
        - inverse: moneda -> VES (moneda más débil)
        - via_usd: Triangulación por USD
        - undefined: VES (moneda base)
        """
    )

    # === OBLIGACIONES TRIBUTARIAS ===

    applies_igtf: bool = Field(
        False,
        description="¿Aplica IGTF para esta moneda? (Divisas: True, VES: False)"
    )

    # Acepta string, float, int
    igtf_rate: Union[str, float, int] = Field(
        "3.00",
        description="Tasa de IGTF (default: 3%, acepta: '3.00', 3.00, 3)"
    )

    igtf_exempt: bool = Field(
        False,
        description="Exención especial de IGTF"
    )

    # Acepta string, float, int (opcional)
    igtf_min_amount: Optional[Union[str, float, int]] = Field(
        None,
        description="Monto mínimo en moneda local para aplicar IGTF (opcional)"
    )

    # === ACTUALIZACIÓN AUTOMÁTICA ===

    rate_update_method: RateUpdateMethod = Field(
        RateUpdateMethod.MANUAL,
        description="Método de actualización de tasas"
    )

    rate_source_url: Optional[str] = Field(
        None,
        max_length=500,
        description="URL de API o scraping para actualización automática"
    )

    # Notas
    notes: Optional[str] = Field(
        None,
        max_length=2000,
        description="Notas adicionales sobre la moneda"
    )

    @validator('code')
    def code_must_be_valid_iso(cls, v):
        """Valida que el código sea ISO 4217 válido"""
        return validate_currency_code(v)

    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        """Valida que el símbolo no esté vacío"""
        if not v or v.isspace():
            raise ValueError('El símbolo no puede estar vacío')
        return v.strip()

    @validator('exchange_rate', pre=True)
    def parse_exchange_rate(cls, v):
        """
        Convierte exchange_rate a Decimal, aceptando:
        - String: "36.5", "36.5000000000"
        - Float: 36.5
        - Int: 36
        """
        if isinstance(v, Decimal):
            if v <= 0:
                raise ValueError('La tasa de cambio debe ser mayor a 0')
            return v

        try:
            # Convertir a string primero, luego a Decimal
            rate = Decimal(str(v))
            if rate <= 0:
                raise ValueError('La tasa de cambio debe ser mayor a 0')
            return rate
        except (ValueError, TypeError) as e:
            raise ValueError(f'Tasa de cambio inválida: {v}. Use formato numérico (ej: "36.5" o 36.5)') from e

    @validator('igtf_rate', pre=True)
    def parse_igtf_rate(cls, v):
        """
        Convierte igtf_rate a Decimal, aceptando string, float o int.
        """
        if isinstance(v, Decimal):
            if v < 0 or v > 100:
                raise ValueError('La tasa de IGTF debe estar entre 0 y 100')
            return v

        try:
            rate = Decimal(str(v))
            if rate < 0 or rate > 100:
                raise ValueError('La tasa de IGTF debe estar entre 0 y 100')
            return rate
        except (ValueError, TypeError) as e:
            raise ValueError(f'Tasa de IGTF inválida: {v}. Use formato numérico (ej: "3.00" o 3.00)') from e

    @validator('igtf_min_amount', pre=True)
    def parse_igtf_min_amount(cls, v):
        """
        Convierte igtf_min_amount a Decimal si está presente.
        """
        if v is None:
            return None

        if isinstance(v, Decimal):
            if v < 0:
                raise ValueError('El monto mínimo de IGTF no puede ser negativo')
            return v

        try:
            amount = Decimal(str(v))
            if amount < 0:
                raise ValueError('El monto mínimo de IGTF no puede ser negativo')
            return amount
        except (ValueError, TypeError) as e:
            raise ValueError(f'Monto mínimo de IGTF inválido: {v}. Use formato numérico') from e

    @root_validator(skip_on_failure=True)
    def validate_base_currency(cls, values):
        """
        Validación para moneda base:
        - Si es VES, conversion_method debe ser None/undefined
        - Si NO es VES y es base, aplicar validaciones específicas
        """
        is_base = values.get('is_base_currency', False)
        code = values.get('code', '').upper()
        method = values.get('conversion_method')

        if is_base:
            if code != 'VES':
                raise ValueError(
                    'Solo VES (Bolívar) puede ser moneda base en Venezuela. '
                    'Si necesitas otra moneda base, usa conversion_method="via_usd"'
                )

            # VES no debe tener método de conversión
            if method is not None and method != ConversionMethod.UNDEFINED:
                values['conversion_method'] = ConversionMethod.UNDEFINED

        return values

    @root_validator(skip_on_failure=True)
    def calculate_conversion_factor(cls, values):
        """
        Calcula automáticamente el factor de conversión según la lógica venezolana:

        1. Si es VES (Bolívar): factor = None (moneda base)
        2. Si es más fuerte que VES (USD, EUR): factor = 1 / exchange_rate
        3. Si es más débil (COP en frontera): factor = exchange_rate

        Nota: No guardamos el factor aquí, solo validamos la lógica.
        El cálculo real se hace en el servicio.
        """
        code = values.get('code', '').upper()
        rate = values.get('exchange_rate')
        method = values.get('conversion_method')

        if code == 'VES':
            # VES no tiene factor de conversión
            if method and method != ConversionMethod.UNDEFINED:
                raise ValueError('VES no debe tener conversion_method')
        elif method == ConversionMethod.DIRECT:
            # Moneda más fuerte: factor = 1 / tasa
            if rate and rate > 0:
                # El factor será calculado en el servicio
                pass
        elif method == ConversionMethod.INVERSE:
            # Moneda más débil: factor = tasa
            pass

        return values

    @root_validator(skip_on_failure=True)
    def validate_igtf_configuration(cls, values):
        """
        Valida configuración de IGTF según lógica venezolana:

        - VES: NO aplica IGTF (applies_igtf = False)
        - Divisas (USD, EUR): SÍ aplica IGTF (applies_igtf = True)
        - Si aplica IGTF, debe tener tasa definida
        """
        code = values.get('code', '').upper()
        applies_igtf = values.get('applies_igtf', False)
        igtf_rate = values.get('igtf_rate')

        if code == 'VES':
            # VES nunca aplica IGTF
            if applies_igtf:
                raise ValueError('VES (Bolívar) no puede aplicar IGTF. Es moneda nacional.')
            values['applies_igtf'] = False
            values['igtf_exempt'] = True  # VES está exento por defecto
        else:
            # Divisas usualmente aplican IGTF
            if applies_igtf and igtf_rate is None:
                raise ValueError(
                    'Si aplica IGTF, debe especificar igtf_rate (default: 3%)'
                )

        return values

    class Config:
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class CurrencyUpdate(BaseModel):
    """Schema para actualizar moneda existente"""

    name: Optional[str] = Field(None, min_length=1, max_length=100)
    symbol: Optional[str] = Field(None, min_length=1, max_length=10)

    exchange_rate: Optional[Decimal] = Field(None, gt=0, decimal_places=10)
    decimal_places: Optional[int] = Field(None, ge=0, le=10)
    is_active: Optional[bool] = None

    conversion_method: Optional[ConversionMethod] = None

    applies_igtf: Optional[bool] = None
    igtf_rate: Optional[Decimal] = Field(None, ge=0, le=100, decimal_places=2)
    igtf_exempt: Optional[bool] = None
    igtf_min_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    rate_update_method: Optional[RateUpdateMethod] = None
    rate_source_url: Optional[str] = Field(None, max_length=500)

    notes: Optional[str] = Field(None, max_length=2000)

    @validator('symbol')
    def symbol_must_be_valid(cls, v):
        if v is not None:
            if not v or v.isspace():
                raise ValueError('El símbolo no puede estar vacío')
            return v.strip()
        return v


class CurrencyRateUpdate(BaseModel):
    """
    Schema para actualizar la tasa de cambio con registro histórico.

    Incluye razón del cambio y metadata para auditoría.
    """

    new_rate: Decimal = Field(
        ...,
        gt=0,
        decimal_places=10,
        description="Nueva tasa de cambio (hasta 10 decimales)"
    )

    change_reason: Optional[str] = Field(
        None,
        max_length=1000,
        description="Razón del cambio (ej: 'Actualización BCV', 'Corrección manual')"
    )

    change_type: Literal["manual", "automatic_api", "scheduled", "correction"] = Field(
        "manual",
        description="Tipo de cambio"
    )

    change_source: Optional[str] = Field(
        None,
        max_length=100,
        description="Fuente del cambio (ej: 'api_bcv', 'user_admin')"
    )

    provider_metadata: Optional[dict] = Field(
        None,
        description="Metadata adicional del proveedor (ej: timestamp API, response code)"
    )

    @validator('new_rate')
    def rate_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('La tasa debe ser mayor a 0')
        return v


class CurrencyResponse(BaseModel):
    """Response completo de moneda con todos los campos"""

    id: int
    company_id: int
    code: str
    name: str
    symbol: str
    exchange_rate: Decimal
    decimal_places: int
    is_base_currency: bool
    is_active: bool

    # Factor de conversión
    conversion_method: Optional[str]
    conversion_factor: Optional[Decimal]

    # IGTF
    applies_igtf: bool
    igtf_rate: Optional[Decimal]
    igtf_exempt: bool
    igtf_min_amount: Optional[Decimal]

    # Actualización
    rate_update_method: str
    last_rate_update: Optional[datetime]
    next_rate_update: Optional[datetime]
    rate_source_url: Optional[str]

    # Timestamps
    created_at: datetime
    updated_at: datetime

    # Usuario
    created_by: Optional[int]
    updated_by: Optional[int]

    notes: Optional[str]

    class Config:
        from_attributes = True  # Pydantic v2: from_orm
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class CurrencyRateHistoryResponse(BaseModel):
    """Response de historial de tasas"""

    id: int
    currency_id: int
    company_id: int

    # Cambios
    old_rate: Decimal
    new_rate: Decimal
    rate_difference: Decimal
    rate_variation_percent: Optional[Decimal]

    # Metadata
    changed_by: Optional[int]
    change_type: str
    change_source: Optional[str]
    changed_at: datetime
    change_reason: Optional[str]

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


class IGTFConfigCreate(BaseModel):
    """Schema para crear configuración de IGTF"""

    company_id: int
    currency_id: int

    # Contribuyente especial
    is_special_contributor: bool = Field(
        False,
        description="La empresa es contribuyente especial de IGTF"
    )

    # Tasa
    igtf_rate: Decimal = Field(
        Decimal("3.00"),
        ge=0,
        le=100,
        decimal_places=2,
        description="Tasa de IGTF (default: 3%)"
    )

    # Montos mínimos
    min_amount_local: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    min_amount_foreign: Optional[Decimal] = Field(None, ge=0, decimal_places=2)

    # Exenciones
    is_exempt: bool = Field(False)
    exempt_transactions: Optional[List[str]] = Field(
        None,
        description="Tipos de transacción exentas"
    )

    # Métodos de pago aplicables
    applicable_payment_methods: Optional[List[str]] = Field(
        None,
        description="Métodos de pago que aplican IGTF"
    )

    # Vigencia
    valid_from: datetime = Field(default_factory=datetime.now)
    valid_until: Optional[datetime] = Field(None)

    notes: Optional[str] = None


class IGTFConfigResponse(BaseModel):
    """Response de configuración IGTF"""

    id: int
    company_id: int
    currency_id: int

    is_special_contributor: bool
    igtf_rate: Decimal
    min_amount_local: Optional[Decimal]
    min_amount_foreign: Optional[Decimal]

    is_exempt: bool
    exempt_transactions: Optional[List[str]]
    applicable_payment_methods: Optional[List[str]]

    valid_from: datetime
    valid_until: Optional[datetime]

    created_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            Decimal: str,
            datetime: lambda v: v.isoformat()
        }


# ==================== EJEMPLOS DE USO ====================

class CurrencyExamples:
    """Ejemplos de uso de schemas con lógica venezolana"""

    @staticmethod
    def example_usd():
        """Ejemplo: Dólar (moneda más fuerte)"""
        return CurrencyCreate(
            code="USD",
            name="US Dollar",
            symbol="$",
            exchange_rate=Decimal("36.5000000000"),
            decimal_places=2,
            is_base_currency=False,
            conversion_method=ConversionMethod.DIRECT,  # VES -> USD
            applies_igtf=True,  # ¡APLICA IGTF!
            igtf_rate=Decimal("3.00"),
            igtf_min_amount=Decimal("1000"),  # $1000 USD
            rate_update_method=RateUpdateMethod.API_BCV,
            rate_source_url="https://www.bcv.org.ve"
        )

    @staticmethod
    def example_ves():
        """Ejemplo: Bolívar (moneda base)"""
        return CurrencyCreate(
            code="VES",
            name="Bolívar Soberano",
            symbol="Bs",
            exchange_rate=Decimal("1.0000000000"),
            decimal_places=2,
            is_base_currency=True,  # ¡MONEDA BASE!
            conversion_method=None,  # No aplica para moneda base
            applies_igtf=False,  # NO aplica IGTF (moneda nacional)
            igtf_exempt=True,
            rate_update_method=RateUpdateMethod.MANUAL
        )

    @staticmethod
    def example_cop():
        """Ejemplo: Peso Colombiano (más débil, frontera)"""
        return CurrencyCreate(
            code="COP",
            name="Colombian Peso",
            symbol="$",
            exchange_rate=Decimal("0.0091000000"),  # 1 COP = 0.0091 VES
            decimal_places=2,
            is_base_currency=False,
            conversion_method=ConversionMethod.INVERSE,  # COP -> VES
            applies_igtf=False,  # No aplica IGTF (moneda local fronteriza)
            rate_update_method=RateUpdateMethod.MANUAL
        )

    @staticmethod
    def example_eur():
        """Ejemplo: Euro (divisa, aplica IGTF)"""
        return CurrencyCreate(
            code="EUR",
            name="Euro",
            symbol="€",
            exchange_rate=Decimal("39.8000000000"),
            decimal_places=2,
            is_base_currency=False,
            conversion_method=ConversionMethod.DIRECT,
            applies_igtf=True,  # ¡APLICA IGTF!
            igtf_rate=Decimal("3.00"),
            rate_update_method=RateUpdateMethod.API_FIXER,
            rate_source_url="https://api.fixer.io/latest"
        )


# ==================== SCHEMAS ADICIONALES PARA FRONTEND ====================

class CurrencyConversionRequest(BaseModel):
    """Request para conversión de monedas (POST)"""
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., gt=0, decimal_places=2)

    class Config:
        json_schema_extra = {
            "example": {
                "from_currency": "USD",
                "to_currency": "EUR",
                "amount": 100
            }
        }


class IGTFCalculationRequest(BaseModel):
    """Request para cálculo de IGTF (POST)"""
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency_id: int = Field(..., gt=0)
    payment_method: str = Field("transfer")

    class Config:
        json_schema_extra = {
            "example": {
                "amount": 100,
                "currency_id": 1,
                "payment_method": "transfer"
            }
        }


# ==================== SISTEMA ESCRITORIO: SCHEMAS ADICIONALES ====================

# ✅ SISTEMA ESCRITORIO: Departamentos
class DepartmentBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None
    utility_percentage: float = 30.0


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    utility_percentage: Optional[float] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class Department(DepartmentBase):
    id: int
    company_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Vendedores
class SellerBase(BaseModel):
    code: str
    name: str
    status: str = '01'  # 01=Activo, 02=Inactivo
    percent_sales: float = 0.0
    percent_receivable: float = 0.0
    user_code: Optional[str] = None
    percent_gerencial_debit_note: float = 0.0
    percent_gerencial_credit_note: float = 0.0
    percent_returned_check: float = 0.0


class SellerCreate(SellerBase):
    pass


class SellerUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    percent_sales: Optional[float] = None
    percent_receivable: Optional[float] = None
    user_code: Optional[str] = None
    percent_gerencial_debit_note: Optional[float] = None
    percent_gerencial_credit_note: Optional[float] = None
    percent_returned_check: Optional[float] = None

    class Config:
        from_attributes = True


class Seller(SellerBase):
    id: int
    company_id: int

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Grupos de clientes
class ClientGroupBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class ClientGroupCreate(ClientGroupBase):
    pass


class ClientGroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class ClientGroup(ClientGroupBase):
    id: int
    company_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Áreas de ventas
class AreasSalesBase(BaseModel):
    code: str
    name: str
    description: Optional[str] = None


class AreasSalesCreate(AreasSalesBase):
    pass


class AreasSalesUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class AreasSales(AreasSalesBase):
    id: int
    company_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Tipos de impuesto (Categorías)
class TaxTypeBase(BaseModel):
    code: str  # "1", "2", "3", "4", etc. (STRING for backward compatibility)
    description: str  # "General", "Reducida", "Exento", etc.
    fiscal_printer_position: Optional[int] = None
    # Optional old fields for backward compatibility
    name: Optional[str] = None
    aliquot: Optional[float] = None


class TaxTypeCreate(TaxTypeBase):
    pass


class TaxTypeUpdate(BaseModel):
    description: Optional[str] = None
    fiscal_printer_position: Optional[int] = None
    status: Optional[bool] = None
    is_active: Optional[bool] = None
    name: Optional[str] = None
    aliquot: Optional[float] = None

    class Config:
        from_attributes = True


class TaxType(TaxTypeBase):
    id: int
    company_id: int
    status: bool
    is_active: bool

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Impuestos (Códigos específicos)
class TaxBase(BaseModel):
    code: str  # "01", "02", "03", "EX", "06", etc.
    description: str  # "Alicuota General", "Exento", etc.
    short_description: str  # "16%", "Exento", "8%", etc.
    aliquot: float  # 16, 8, 31, 0
    tax_type_id: int  # FK to tax_types
    status: bool = True


class TaxCreate(TaxBase):
    pass


class TaxUpdate(BaseModel):
    description: Optional[str] = None
    short_description: Optional[str] = None
    aliquot: Optional[float] = None
    tax_type_id: Optional[int] = None
    status: Optional[bool] = None
    is_active: Optional[bool] = None

    class Config:
        from_attributes = True


class Tax(TaxBase):
    id: int
    company_id: int
    is_active: bool

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Unidades de producto
class ProductUnitBase(BaseModel):
    product_id: int
    unit_id: int
    correlative: int
    main_unit: bool = False
    conversion_factor: float = 0
    unit_type: int = 1  # 1=Principal x Secundaria, 2=Secundaria x Principal
    show_in_screen: bool = False
    is_for_buy: bool = True
    is_for_sale: bool = True

    # Costos
    unitary_cost: Optional[float] = None
    calculated_cost: Optional[float] = None
    average_cost: Optional[float] = None
    perc_waste_cost: float = 0
    perc_handling_cost: float = 0
    perc_operating_cost: float = 0
    perc_additional_cost: float = 0

    # Precios
    maximum_price: Optional[float] = None
    offer_price: Optional[float] = None
    higher_price: Optional[float] = None
    minimum_price: Optional[float] = None

    # Utilidades por precio
    perc_maximum_price: Optional[float] = None
    perc_offer_price: Optional[float] = None
    perc_higher_price: Optional[float] = None
    perc_minimum_price: Optional[float] = None

    # Porcentajes de costo
    perc_freight_cost: float = 0
    perc_discount_provider: float = 0

    # Medidas físicas
    lenght: float = 0
    height: float = 0
    width: float = 0
    weight: float = 0
    capacitance: float = 0


class ProductUnitCreate(ProductUnitBase):
    pass


class ProductUnitUpdate(BaseModel):
    unit_id: Optional[int] = None
    main_unit: Optional[bool] = None
    conversion_factor: Optional[float] = None
    unit_type: Optional[int] = None
    show_in_screen: Optional[bool] = None
    is_for_buy: Optional[bool] = None
    is_for_sale: Optional[bool] = None
    unitary_cost: Optional[float] = None
    calculated_cost: Optional[float] = None
    average_cost: Optional[float] = None
    perc_waste_cost: Optional[float] = None
    perc_handling_cost: Optional[float] = None
    perc_operating_cost: Optional[float] = None
    perc_additional_cost: Optional[float] = None
    maximum_price: Optional[float] = None
    offer_price: Optional[float] = None
    higher_price: Optional[float] = None
    minimum_price: Optional[float] = None
    perc_maximum_price: Optional[float] = None
    perc_offer_price: Optional[float] = None
    perc_higher_price: Optional[float] = None
    perc_minimum_price: Optional[float] = None
    perc_freight_cost: Optional[float] = None
    perc_discount_provider: Optional[float] = None
    lenght: Optional[float] = None
    height: Optional[float] = None
    width: Optional[float] = None
    weight: Optional[float] = None
    capacitance: Optional[float] = None

    class Config:
        from_attributes = True


class ProductUnit(ProductUnitBase):
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Producto con unidades
class ProductWithUnits(Product):
    """Producto con todas sus unidades"""
    product_units: List[ProductUnit] = []

    class Config:
        from_attributes = True


# ==================== ✅ SISTEMA ESCRITORIO: OPERACIONES DE VENTA ====================

# ✅ SISTEMA ESCRITORIO: Operación de venta principal
class SalesOperationBase(BaseModel):
    """Schema base para operaciones de venta"""
    # ✅ Identificación
    correlative: int
    operation_type: str  # BUDGET, ORDER, DELIVERYNOTE, BILL, CREDITNOTE, DEBITNOTE
    document_no: Optional[str] = None
    document_no_internal: Optional[str] = ""
    control_no: Optional[str] = None

    # ✅ Fechas
    emission_date: datetime
    register_date: datetime
    register_hour: Optional[str] = None
    expiration_date: Optional[datetime] = None

    # ✅ Cliente (información duplicada para historial)
    client_id: int
    client_name: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None
    client_name_fiscal: int = 1

    # ✅ Ubicación
    seller: str = "00"
    store: str = "00"
    locations: str = "00"
    user_code: Optional[str] = None
    station: str = "00"

    # ✅ Estados
    wait: bool = False
    pending: bool = True
    canceled: bool = False
    delivered: bool = False
    begin_used: bool = False

    # ✅ Totales de detalles
    total_amount: float = 0
    total_net_details: float = 0
    total_tax_details: float = 0
    total_details: float = 0

    # ✅ Descuentos y fletes
    percent_discount: float = 0
    discount: float = 0
    percent_freight: float = 0
    freight: float = 0

    # ✅ Totales con impuestos
    total_net: float = 0
    total_tax: float = 0
    total: float = 0

    # ✅ Pagos
    credit: float = 0
    cash: float = 0

    # ✅ Costos
    total_net_cost: float = 0
    total_tax_cost: float = 0
    total_cost: float = 0

    # ✅ Configuración de precio
    type_price: int = 0
    total_count_details: float = 0

    # ✅ Flete
    freight_tax: str = "01"
    freight_aliquot: float = 16

    # ✅ Retenciones
    total_retention_tax: float = 0
    total_retention_municipal: float = 0
    total_retention_islr: float = 0
    retention_tax_prorration: float = 0
    retention_islr_prorration: float = 0
    retention_municipal_prorration: float = 0

    # ✅ Total operación
    total_operation: float = 0

    # ✅ Impresora fiscal
    fiscal_impresion: bool = False
    fiscal_printer_serial: str = ""
    fiscal_printer_z: str = ""
    fiscal_printer_date: Optional[datetime] = None

    # ✅ Configuración adicional
    coin_code: str = "01"
    sale_point: bool = False
    restorant: bool = False

    # ✅ Envío
    address_send: str = ""
    contact_send: str = ""
    phone_send: str = ""
    total_weight: float = 0

    # ✅ IGTF
    free_tax: bool = False
    total_exempt: float = 0
    base_igtf: float = 0
    percent_igtf: float = 0
    igtf: float = 0

    # ✅ Orden de compra relacionada
    shopping_order_document_no: str = ""
    shopping_order_date: Optional[datetime] = None

    # ✅ Comentarios
    operation_comments: Optional[str] = None
    description: Optional[str] = None

    # ✅ SISTEMA ESCRITORIO: Detalles de la operación (items/products)
    details: Optional[List['SalesOperationDetailCreate']] = None

    @validator('operation_type')
    def validate_operation_type(cls, v):
        valid_types = ['BUDGET', 'ORDER', 'DELIVERYNOTE', 'BILL', 'CREDITNOTE', 'DEBITNOTE']
        if v not in valid_types:
            raise ValueError(f'operation_type must be one of: {valid_types}')
        return v

    @validator('client_name_fiscal')
    def validate_client_name_fiscal(cls, v):
        if v not in [0, 1, 2]:
            raise ValueError('client_name_fiscal must be 0 (Ordinario), 1 (No Contribuyente), or 2 (Formal)')
        return v


class SalesOperationCreate(SalesOperationBase):
    """Schema para crear operación de venta"""
    pass


class SalesOperationUpdate(BaseModel):
    """Schema para actualizar operación de venta (todos los campos opcionales)"""
    document_no: Optional[str] = None
    document_no_internal: Optional[str] = None
    control_no: Optional[str] = None
    emission_date: Optional[datetime] = None
    register_date: Optional[datetime] = None
    register_hour: Optional[str] = None
    expiration_date: Optional[datetime] = None
    client_id: Optional[int] = None
    client_name: Optional[str] = None
    client_tax_id: Optional[str] = None
    client_address: Optional[str] = None
    client_phone: Optional[str] = None
    client_name_fiscal: Optional[int] = None
    seller: Optional[str] = None
    store: Optional[str] = None
    locations: Optional[str] = None
    user_code: Optional[str] = None
    station: Optional[str] = None
    wait: Optional[bool] = None
    pending: Optional[bool] = None
    canceled: Optional[bool] = None
    delivered: Optional[bool] = None
    begin_used: Optional[bool] = None
    total_amount: Optional[float] = None
    total_net_details: Optional[float] = None
    total_tax_details: Optional[float] = None
    total_details: Optional[float] = None
    percent_discount: Optional[float] = None
    discount: Optional[float] = None
    percent_freight: Optional[float] = None
    freight: Optional[float] = None
    total_net: Optional[float] = None
    total_tax: Optional[float] = None
    total: Optional[float] = None
    credit: Optional[float] = None
    cash: Optional[float] = None
    total_net_cost: Optional[float] = None
    total_tax_cost: Optional[float] = None
    total_cost: Optional[float] = None
    type_price: Optional[int] = None
    total_count_details: Optional[float] = None
    freight_tax: Optional[str] = None
    freight_aliquot: Optional[float] = None
    total_retention_tax: Optional[float] = None
    total_retention_municipal: Optional[float] = None
    total_retention_islr: Optional[float] = None
    retention_tax_prorration: Optional[float] = None
    retention_islr_prorration: Optional[float] = None
    retention_municipal_prorration: Optional[float] = None
    total_operation: Optional[float] = None
    fiscal_impresion: Optional[bool] = None
    fiscal_printer_serial: Optional[str] = None
    fiscal_printer_z: Optional[str] = None
    fiscal_printer_date: Optional[datetime] = None
    coin_code: Optional[str] = None
    sale_point: Optional[bool] = None
    restorant: Optional[bool] = None
    address_send: Optional[str] = None
    contact_send: Optional[str] = None
    phone_send: Optional[str] = None
    total_weight: Optional[float] = None
    free_tax: Optional[bool] = None
    total_exempt: Optional[float] = None
    base_igtf: Optional[float] = None
    percent_igtf: Optional[float] = None
    igtf: Optional[float] = None
    shopping_order_document_no: Optional[str] = None
    shopping_order_date: Optional[datetime] = None
    operation_comments: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True


class SalesOperation(SalesOperationBase):
    """Schema completo de operación de venta"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Montos en diferentes monedas
class SalesOperationCoinBase(BaseModel):
    """Schema base para montos de operación en diferentes monedas"""
    sales_operation_id: int
    main_correlative: int
    coin_code: str
    factor_type: int
    buy_aliquot: float
    sales_aliquot: float
    total_net_details: float = 0
    total_tax_details: float = 0
    total_details: float = 0
    discount: float = 0
    freight: float = 0
    total_net: float = 0
    total_tax: float = 0
    total: float = 0
    credit: float = 0
    cash: float = 0
    total_net_cost: float = 0
    total_tax_cost: float = 0
    total_cost: float = 0
    total_operation: float = 0
    total_retention_tax: float = 0
    total_retention_municipal: float = 0
    total_retention_islr: float = 0
    retention_tax_prorration: float = 0
    retention_islr_prorration: float = 0
    retention_municipal_prorration: float = 0
    total_exempt: float = 0


class SalesOperationCoinCreate(SalesOperationCoinBase):
    """Schema para crear montos en moneda"""
    pass


class SalesOperationCoin(SalesOperationCoinBase):
    """Schema completo de montos en moneda"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Detalles de la operación (líneas)
class SalesOperationDetailBase(BaseModel):
    """Schema base para detalles de operación de venta"""
    sales_operation_id: int
    main_correlative: int
    line: int

    # ✅ Producto (información duplicada)
    code_product: Optional[str] = None
    description_product: Optional[str] = None
    referenc: Optional[str] = None
    mark: Optional[str] = None
    model: Optional[str] = None

    # ✅ Ubicación
    store: Optional[str] = None
    locations: Optional[str] = None

    # ✅ Unidad
    unit: Optional[int] = None
    conversion_factor: float = 0
    unit_type: int = 0

    # ✅ Cantidades y Precios
    amount: float = 0
    unitary_cost: float = 0
    sale_tax: str = "01"
    sale_aliquot: float = 0
    price: float = 0
    type_price: int = 0

    # ✅ Costos
    total_net_cost: float = 0
    total_tax_cost: float = 0
    total_cost: float = 0

    # ✅ Precios Brutos
    total_net_gross: float = 0
    total_tax_gross: float = 0
    total_gross: float = 0

    # ✅ Descuentos
    percent_discount: float = 0
    discount: float = 0

    # ✅ Totales
    total_net: float = 0
    total_tax: float = 0
    total: float = 0

    # ✅ Inventario
    pending_amount: float = 0
    buy_tax: str = "01"
    buy_aliquot: float = 0
    update_inventory: bool = False
    amount_released_by_load_order: float = 0
    amount_discharged_by_load_delivery_note: float = 0

    # ✅ Adicionales
    product_type: Optional[str] = None
    description: Optional[str] = None
    technician: str = "00"
    coin_code: str = "01"
    total_weight: float = 0


class SalesOperationDetailCreate(BaseModel):
    """Schema para crear detalle de operación (sin campos autogenerados)"""
    line: int
    code_product: str
    description_product: str
    referenc: Optional[str] = None
    mark: Optional[str] = None
    model: Optional[str] = None
    store: str = "00"
    locations: str = "00"
    unit: int = 1
    conversion_factor: float = 1
    unit_type: int = 0
    amount: float
    unitary_cost: float = 0
    price: float
    sale_tax: str = "01"
    sale_aliquot: float = 16
    total_net: float
    total_tax: float
    total: float


class SalesOperationDetail(SalesOperationDetailBase):
    """Schema completo de detalle de operación"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Montos de detalles en diferentes monedas
class SalesOperationDetailCoinBase(BaseModel):
    """Schema base para montos de detalle en diferentes monedas"""
    main_correlative: int
    main_line: int
    coin_code: str
    unitary_cost: float = 0
    total_net_cost: float = 0
    total_tax_cost: float = 0
    total_cost: float = 0
    total_net_gross: float = 0
    total_tax_gross: float = 0
    total_gross: float = 0
    discount: float = 0
    total_net: float = 0
    total_tax: float = 0
    total: float = 0


class SalesOperationDetailCoinCreate(SalesOperationDetailCoinBase):
    """Schema para crear montos de detalle en moneda"""
    pass


class SalesOperationDetailCoin(SalesOperationDetailCoinBase):
    """Schema completo de montos de detalle en moneda"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Impuestos del documento
class SalesOperationTaxBase(BaseModel):
    """Schema base para impuestos de operación"""
    sales_operation_id: int
    main_correlative: int
    line: int
    taxe_code: str
    aliquot: float
    taxable: float = 0
    tax: float = 0
    tax_type: int


class SalesOperationTaxCreate(SalesOperationTaxBase):
    """Schema para crear impuesto de operación"""
    pass


class SalesOperationTax(SalesOperationTaxBase):
    """Schema completo de impuesto de operación"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Impuestos en diferentes monedas
class SalesOperationTaxCoinBase(BaseModel):
    """Schema base para impuestos en diferentes monedas"""
    main_correlative: int
    main_taxe_code: str
    main_line: int
    coin_code: str
    taxable: float = 0
    tax: float = 0


class SalesOperationTaxCoinCreate(SalesOperationTaxCoinBase):
    """Schema para crear impuesto en moneda"""
    pass


class SalesOperationTaxCoin(SalesOperationTaxCoinBase):
    """Schema completo de impuesto en moneda"""
    id: int
    company_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Operación de venta con relaciones completas
class SalesOperationWithDetails(SalesOperation):
    """Operación de venta con todos sus detalles, monedas e impuestos"""
    coins: List[SalesOperationCoin] = []
    details: List[SalesOperationDetail] = []
    taxes: List[SalesOperationTax] = []

    class Config:
        from_attributes = True


# ✅ SISTEMA ESCRITORIO: Operación de venta con cliente
class SalesOperationWithClient(SalesOperation):
    """Operación de venta con información del cliente"""
    client: Optional["Customer"] = None

    class Config:
        from_attributes = True
