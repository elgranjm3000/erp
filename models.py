from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Boolean, Text, Numeric, Date, Time
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
    exchange_rates = relationship("ExchangeRateHistory", cascade="all, delete-orphan")  # ✅ HISTORIAL TASAS
    daily_rates = relationship("DailyRate", back_populates="company", cascade="all, delete-orphan")  # ✅ TASAS DIARIAS
    coin_history = relationship("CoinHistory", cascade="all, delete-orphan")  # ✅ SISTEMA ESCRITORIO: Historial de monedas
    # ✅ SISTEMA ESCRITORIO: Nuevas relaciones
    departments = relationship("Department")  # ✅ DEPARTAMENTOS
    sellers = relationship("Seller")  # ✅ VENDEDORES
    client_groups = relationship("ClientGroup")  # ✅ GRUPOS DE CLIENTES
    areas_sales = relationship("AreasSales")  # ✅ ÁREAS DE VENTAS
    tax_types = relationship("TaxType")  # ✅ TIPOS DE IMPUESTOS

# Cliente
class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # ✅ Campos básicos
    name = Column(String(60), index=True)
    email = Column(String(60), index=True)
    phone = Column(String(11))
    address = Column(String(200))
    tax_id = Column(String(20))  # RIF/CI del cliente
    latitude = Column(Float, nullable=True)  # ✅ UBICACIÓN: Latitud para mapa
    longitude = Column(Float, nullable=True)  # ✅ UBICACIÓN: Longitud para mapa

    # ✅ SISTEMA ESCRITORIO: Clasificación fiscal
    name_fiscal = Column(Integer, default=1)  # ✅ 0=Ordinario, 1=No Contribuyente, 2=Formal
    client_type = Column(String(2), default='01')  # ✅ 01=Juridico, 02=Natural, 03=Government

    # ✅ SISTEMA ESCRITORIO: Retenciones
    retention_tax_agent = Column(Boolean, default=False)  # ✅ Agente de retención IVA
    retention_municipal_agent = Column(Boolean, default=False)  # ✅ Agente de retención municipal
    retention_islr_agent = Column(Boolean, default=False)  # ✅ Agente de retención ISLR

    # ✅ SISTEMA ESCRITORIO: Crédito
    credit_days = Column(Integer, default=0)  # ✅ Días de crédito
    credit_limit = Column(Float, default=0)  # ✅ Límite de crédito
    allow_expired_balance = Column(Boolean, default=False)  # ✅ Permitir vender con saldo vencido

    # ✅ SISTEMA ESCRITORIO: Asignaciones
    seller_id = Column(Integer, ForeignKey('sellers.id'), nullable=True)  # ✅ Vendedor asignado
    client_group_id = Column(Integer, ForeignKey('client_groups.id'), nullable=True)  # ✅ Grupo de cliente
    area_sales_id = Column(Integer, ForeignKey('areas_sales.id'), nullable=True)  # ✅ Área de ventas

    # ✅ SISTEMA ESCRITORIO: Precios y descuentos
    sale_price = Column(Integer, default=1)  # ✅ 0=Max, 1=Oferta, 2=Mayor, 3=Min, 4=Variable
    discount = Column(Float, default=0)  # ✅ Descuento fijo del cliente

    # ✅ SISTEMA ESCRITORIO: Estado
    status = Column(String(2), default='01')  # ✅ 01=Activo, 02=Inactivo

    # ✅ SISTEMA ESCRITORIO: Contacto adicional
    contact_name = Column(String(100), nullable=True)  # ✅ Nombre del contacto

    # Relaciones
    invoices = relationship("Invoice", back_populates="customer")
    company = relationship("Company", back_populates="customers")
    seller = relationship("Seller")  # ✅ SISTEMA ESCRITORIO: Vendedor asignado
    client_group = relationship("ClientGroup")  # ✅ SISTEMA ESCRITORIO: Grupo de cliente
    area_sales = relationship("AreasSales")  # ✅ SISTEMA ESCRITORIO: Área de ventas

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
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)  # Moneda de pago (VES)
    reference_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)  # Moneda de referencia (USD)
    exchange_rate = Column(Float, nullable=True)  # Tasa de cambio usada (para registro histórico)
    manual_exchange_rate = Column(Float, nullable=True)  # Tasa manual para override (permite usar tasa diferente a BCV)
    exchange_rate_date = Column(DateTime, nullable=True)  # Fecha en que se registró la tasa de cambio

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

    # ✅ SISTEMA REF: Precios de referencia para Venezuela
    subtotal_reference = Column(Float, nullable=True)  # Subtotal en moneda de referencia (USD)
    subtotal_target = Column(Float, nullable=True)  # Subtotal en moneda de pago (VES)

    # ✅ VENEZUELA: IGTF (Impuesto a Grandes Transacciones Financieras)
    igtf_amount = Column(Float, default=0.0)  # Monto de IGTF calculado
    igtf_percentage = Column(Float, default=0.0)  # Porcentaje aplicado (default 3%)
    igtf_exempt = Column(Boolean, default=False)  # Si la factura está exenta de IGTF

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
    currency = relationship("Currency", foreign_keys=[currency_id])  # ✅ MONEDA: Moneda de pago
    reference_currency = relationship("Currency", foreign_keys=[reference_currency_id])  # ✅ MULTI-MONEDA: Moneda de referencia

# ✅ SISTEMA REF: Historial de tasas de conversión por factura
class InvoiceRateHistory(Base):
    """
    Historial de tasas de cambio usadas en facturas.

    Permite auditoría completa de qué tasa se usó en cada momento,
    crucial para contextos inflacionarios donde las tasas cambian diariamente.
    """
    __tablename__ = 'invoice_rate_history'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # Información de la tasa
    from_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)  # USD
    to_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)    # VES
    exchange_rate = Column(Float, nullable=False)  # Ej: 344.51 Bs/USD

    # Metadatos
    rate_source = Column(String(50))  # 'BCV', 'manual', 'system'
    rate_date = Column(DateTime, default=func.now())  # Cuándo se registró esta tasa
    recorded_at = Column(DateTime, default=func.now())  # Cuándo se creó este registro

    # Relaciones
    invoice = relationship("Invoice", backref="rate_history")
    company = relationship("Company")
    from_currency = relationship("Currency", foreign_keys=[from_currency_id])
    to_currency = relationship("Currency", foreign_keys=[to_currency_id])

# Detalle de la Factura
class InvoiceItem(Base):
    __tablename__ = 'invoice_items'

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'))
    product_id = Column(Integer, ForeignKey('products.id'))
    quantity = Column(Integer)
    price_per_unit = Column(Float)
    total_price = Column(Float)

    # ✅ MONEDA: Cada item puede estar en una moneda diferente
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    exchange_rate = Column(Float, nullable=True)  # Tasa usada para este item
    exchange_rate_date = Column(DateTime, nullable=True)  # Fecha de la tasa
    base_currency_amount = Column(Float, default=0.0)  # Monto convertida a moneda base de la factura

    # ✅ VENEZUELA: Información fiscal por item
    tax_rate = Column(Float, default=16.0)  # Tasa impositiva (16%, 8%, 0%)
    tax_amount = Column(Float, default=0.0)  # IVA por item
    is_exempt = Column(Boolean, default=False)  # Si el item está exento de IVA

    invoice = relationship("Invoice", back_populates="invoice_items")
    product = relationship("Product")
    currency = relationship("Currency")  # ✅ MONEDA

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

    # ✅ Campos básicos
    name = Column(String(60), index=True)
    short_name = Column(String(50))  # ✅ SISTEMA ESCRITORIO: Descripción corta
    description = Column(String(200))
    sku = Column(String(50), index=True)

    # ✅ SISTEMA ESCRITORIO: Clasificación
    mark = Column(String(50))  # Marca del producto
    model = Column(String(50))  # Modelo del producto
    department_id = Column(Integer, ForeignKey('departments.id'))  # ✅ Departamento
    size = Column(String(20))  # ✅ Talla
    color = Column(String(30))  # ✅ Color
    product_type = Column(String(1), default='T')  # ✅ T=Terminado, S=Servicio, C=Compuesto

    # ✅ SISTEMA ESCRITORIO: Impuestos (códigos)
    sale_tax_code = Column(String(2), default='01')  # ✅ 01=16%, 02=31%, 03=8%, 06=Percibido, EX=Exento
    buy_tax_code = Column(String(2), default='01')  # ✅ Código de impuesto de compra

    # ✅ SISTEMA ESCRITORIO: Precios (múltiples niveles)
    price = Column(Integer)  # Precio local (VES) - legacy
    price_usd = Column(Numeric(10, 2), nullable=True)  # Precio referencial en USD
    cost = Column(Numeric(10, 2), nullable=True)  # Costo del producto
    maximum_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio máximo
    offer_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio oferta
    higher_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio mayor
    minimum_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio mínimo
    sale_price_type = Column(Integer, default=0)  # ✅ 0=Max, 1=Oferta, 2=Mayor, 3=Min, 4=Variable

    # ✅ SISTEMA ESCRITORIO: Stock e inventario
    quantity = Column(Integer, default=0)  # Stock actual
    stock_quantity = Column(Integer, default=0)  # ✅ Stock actual (alternativo)
    minimal_stock = Column(Integer, default=10)  # ✅ Stock mínimo
    maximum_stock = Column(Integer, default=0)  # ✅ Stock máximo
    allow_negative_stock = Column(Boolean, default=False)  # ✅ Permitir vender sin stock
    serialized = Column(Boolean, default=False)  # ✅ Usa serial
    use_lots = Column(Boolean, default=False)  # ✅ Usa lotes
    lots_order = Column(Integer, default=0)  # ✅ 0=PEPS, 1=PUPS, 2=Vencimiento

    # ✅ SISTEMA ESCRITORIO: Costeo
    costing_type = Column(Integer, default=0)  # ✅ 0=Promedio, 1=Último, 2=PEPS, 3=UEPS
    calculated_cost = Column(Numeric(10, 2), nullable=True)  # ✅ Costo calculado
    average_cost = Column(Numeric(10, 2), nullable=True)  # ✅ Costo promedio

    # ✅ SISTEMA ESCRITORIO: Descuentos y límites de venta
    discount = Column(Numeric(5, 2), default=0)  # ✅ Descuento del producto
    max_discount = Column(Numeric(5, 2), default=0)  # ✅ Máximo descuento permitido
    minimal_sale = Column(Numeric(10, 2), default=0)  # ✅ Cantidad mínima de venta
    maximal_sale = Column(Numeric(10, 2), default=0)  # ✅ Cantidad máxima de venta

    # ✅ SISTEMA ESCRITORIO: Configuraciones adicionales
    allow_decimal = Column(Boolean, default=True)  # ✅ Permitir decimales en cantidad
    rounding_type = Column(Integer, default=2)  # ✅ Decimales: 0=0,0, 2=0,00, 4=0,0000
    edit_name = Column(Boolean, default=False)  # ✅ Permitir editar nombre en ventas
    take_department_utility = Column(Boolean, default=True)  # ✅ Usar utilidad del departamento

    # ✅ SISTEMA ESCRITORIO: Moneda
    coin = Column(String(2), default='01')  # ✅ 01=Bolívar, 02=Dólar (references COINS)

    # ✅ SISTEMA ESCRITORIO: Garantía
    days_warranty = Column(Integer, default=0)  # ✅ Días de garantía

    # ✅ SISTEMA ESCRITORIO: Estado
    status = Column(String(2), default='01')  # ✅ 01=Activo, 02=Inactivo

    # ✅ Campos legacy (compatibilidad)
    category_id = Column(Integer, ForeignKey('categories.id'))
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    warehouse_id = Column(Integer, ForeignKey('warehouses.id'), nullable=True)  # ✅ Depósito/Almacén del producto

    # Relaciones
    company = relationship("Company", back_populates="products")
    category = relationship("Category", back_populates="products")
    department = relationship("Department")  # ✅ SISTEMA ESCRITORIO: Departamento
    warehouse = relationship("Warehouse")  # ✅ Depósito/Almacén del producto
    currency = relationship("Currency", foreign_keys=[currency_id])  # ✅ Moneda del producto
    inventory_movements = relationship("InventoryMovement", back_populates="product")
    warehouses = relationship("Warehouse", secondary="warehouse_products", back_populates="products")
    purchase_items = relationship("PurchaseItem", back_populates="product")
    prices = relationship("ProductPrice", cascade="all, delete-orphan")  # ✅ MONEDAS: Precios multi-moneda
    # price_history = relationship("ProductPriceHistory", back_populates="product")  # ❌ DESACTIVADO: El modelo no coincide con la BD, causa error en DELETE
    product_units = relationship("ProductUnit", cascade="all, delete-orphan")  # ✅ SISTEMA ESCRITORIO: Unidades del producto


# ✅ SISTEMA ESCRITORIO: Unidades de producto (múltiples unidades por producto)
class ProductUnit(Base):
    __tablename__ = 'product_units'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)  # Producto al que pertenece

    # ✅ Identificación
    correlative = Column(Integer, nullable=False)  # ✅ Secuencia: 1, 2, 3, 4, 5...
    unit_id = Column(Integer, ForeignKey('units.id'), nullable=False)  # ✅ Unidad de medida (references UNITS)

    # ✅ Configuración de unidad
    main_unit = Column(Boolean, default=False)  # ✅ TRUE = unidad principal
    conversion_factor = Column(Numeric(10, 4), default=0)  # ✅ Factor de conversión (principal siempre 0)
    unit_type = Column(Integer, default=1)  # ✅ 1=Principal x Secundaria, 2=Secundaria x Principal

    # ✅ Visibilidad
    show_in_screen = Column(Boolean, default=False)  # ✅ Mostrar de primero
    is_for_buy = Column(Boolean, default=True)  # ✅ Se puede ver en compras
    is_for_sale = Column(Boolean, default=True)  # ✅ Se puede ver en ventas

    # ✅ Costos
    unitary_cost = Column(Numeric(10, 2), nullable=True)  # ✅ Costo unitario (sin impuesto)
    calculated_cost = Column(Numeric(10, 2), nullable=True)  # ✅ Costo calculado
    average_cost = Column(Numeric(10, 2), nullable=True)  # ✅ Costo promedio
    perc_waste_cost = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje de desperdicio
    perc_handling_cost = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje de manejo
    perc_operating_cost = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje de operación
    perc_additional_cost = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje adicional

    # ✅ Precios (4 niveles)
    maximum_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio máximo (sin impuesto)
    offer_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio oferta (sin impuesto)
    higher_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio mayor (sin impuesto)
    minimum_price = Column(Numeric(10, 2), nullable=True)  # ✅ Precio mínimo (sin impuesto)

    # ✅ Porcentajes de utilidad por precio
    perc_maximum_price = Column(Numeric(5, 2), nullable=True)  # ✅ Utilidad precio máximo
    perc_offer_price = Column(Numeric(5, 2), nullable=True)  # ✅ Utilidad precio oferta
    perc_higher_price = Column(Numeric(5, 2), nullable=True)  # ✅ Utilidad precio mayor
    perc_minimum_price = Column(Numeric(5, 2), nullable=True)  # ✅ Utilidad precio mínimo

    # ✅ Porcentajes de costo
    perc_freight_cost = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje de flete
    perc_discount_provider = Column(Numeric(5, 2), default=0)  # ✅ Porcentaje de descuento proveedor

    # ✅ Medidas físicas
    lenght = Column(Numeric(10, 2), default=0)  # ✅ Largo
    height = Column(Numeric(10, 2), default=0)  # ✅ Altura
    width = Column(Numeric(10, 2), default=0)  # ✅ Ancho
    weight = Column(Numeric(10, 2), default=0)  # ✅ Peso
    capacitance = Column(Numeric(10, 2), default=0)  # ✅ Capacidad

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    product = relationship("Product", back_populates="product_units")
    unit = relationship("Unit")

    def __repr__(self):
        return f"<ProductUnit product={self.product_id} unit={self.unit_id} main={self.main_unit}>"

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
    exchange_rate_date = Column(DateTime, nullable=True)  # Fecha en que se registró la tasa de cambio

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

    # ✅ VENEZUELA: IGTF (Impuesto a Grandes Transacciones Financieras)
    igtf_amount = Column(Float, default=0.0)  # Monto de IGTF calculado
    igtf_percentage = Column(Float, default=0.0)  # Porcentaje aplicado (default 3%)
    igtf_exempt = Column(Boolean, default=False)  # Si la compra está exenta de IGTF

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

    # ✅ MONEDA: Cada item puede estar en una moneda diferente
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)
    exchange_rate = Column(Float, nullable=True)  # Tasa usada para este item
    exchange_rate_date = Column(DateTime, nullable=True)  # Fecha de la tasa
    base_currency_amount = Column(Float, default=0.0)  # Monto convertida a moneda base de la compra

    # ✅ VENEZUELA: Información fiscal por item
    tax_rate = Column(Float, default=16.0)  # Tasa impositiva (16%, 8%, 0%)
    tax_amount = Column(Float, default=0.0)  # IVA por item
    is_exempt = Column(Boolean, default=False)  # Si el item está exento de IVA

    purchase = relationship("Purchase", back_populates="purchase_items")
    product = relationship("Product", back_populates="purchase_items")
    currency = relationship("Currency")  # ✅ MONEDA

# Currency class moved to models/currency_config.py (Venezuelan system with IGTF)


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


# ✅ HISTORIAL DE TASAS DE CAMBIO (ExchangeRateHistory)
class ExchangeRateHistory(Base):
    __tablename__ = 'exchange_rate_history'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    from_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    to_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    rate = Column(Float, nullable=False)  # Tasa de cambio: 1 from_currency = rate to_currency

    # Metadatos
    recorded_at = Column(DateTime, default=func.now(), index=True)  # Cuándo se registró esta tasa
    created_at = Column(DateTime, default=func.now())

    # Relaciones
    company = relationship("Company")
    from_currency = relationship("Currency", foreign_keys=[from_currency_id])
    to_currency = relationship("Currency", foreign_keys=[to_currency_id])

    def __repr__(self):
        return f"<ExchangeRate {self.from_currency.code} -> {self.to_currency.code}: {self.rate}>"


# ✅ SISTEMA ESCRITORIO: Historial de monedas (CoinHistory)
class CoinHistory(Base):
    """
    Historial de cambios de tasas de cambio de monedas (Desktop ERP).

    Estructura basada en el sistema desktop venezolano:
    - Registra cada cambio de tasa con fecha y hora separadas
    - Mantiene sales_aliquot y buy_aliquot (tasas de compra y venta)
    - Auditoría completa con usuario que realizó el cambio
    """
    __tablename__ = 'coin_history'

    id = Column(Integer, primary_key=True, index=True)  # ✅ Correlativo auto-increment
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)

    # ✅ Referencia a la moneda (main_code en PostgreSQL)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, index=True)

    # ✅ Tasas de cambio (separadas para compra y venta)
    sales_aliquot = Column(Float, nullable=False, comment='Tasa de venta (cuanto vale en moneda local)')
    buy_aliquot = Column(Float, nullable=False, comment='Tasa de compra')

    # ✅ Fecha y hora del registro (separados como en desktop ERP)
    register_date = Column(Date, nullable=False, index=True, comment='Fecha del registro')
    register_hour = Column(Time, nullable=False, comment='Hora del registro')

    # ✅ Usuario que realizó el cambio
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, comment='Usuario que registró el cambio')

    # Metadatos
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relaciones
    company = relationship("Company")
    currency = relationship("Currency", foreign_keys=[currency_id])
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<CoinHistory {self.currency.code} sales={self.sales_aliquot} buy={self.buy_aliquot} {self.register_date} {self.register_hour}>"


# ✅ PRECIOS DE PRODUCTOS POR MONEDA (ProductPrice)
class ProductPrice(Base):
    __tablename__ = 'product_prices'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)

    price = Column(Float, nullable=False)
    is_base_price = Column(Boolean, default=False)  # True para la moneda principal del producto

    # Metadatos
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    created_at = Column(DateTime, default=func.now())

    # Relaciones
    product = relationship("Product")
    currency = relationship("Currency")

    # Índice único para evitar duplicados
    __table_args__ = (
        {'schema': None}  # Para evitar problemas con SQLAlchemy
    )

    def __repr__(self):
        return f"<ProductPrice product={self.product_id} {self.currency.code}: {self.price}>"


# ✅ AUDITORÍA: Historial de cambios de precios (sistema REF)
class ProductPriceHistory(Base):
    """
    Historial de cambios en el precio USD de los productos.

    Permite auditoría completa de cambios de precios en el sistema REF,
    crucial para economías inflacionarias donde los precios cambian frecuentemente.
    """
    __tablename__ = 'product_price_history'

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # Información del precio
    price_usd_old = Column(Numeric(10, 2), nullable=True)  # Precio anterior
    price_usd_new = Column(Numeric(10, 2), nullable=False)  # Precio nuevo

    # Metadatos del cambio
    changed_at = Column(DateTime, default=func.now())
    changed_by = Column(Integer, ForeignKey('users.id'), nullable=True)  # Usuario que hizo el cambio
    change_reason = Column(String(200), nullable=True)  # Razón del cambio (opcional)
    change_source = Column(String(50), default='manual')  # 'manual', 'system', 'import'

    # Relaciones
    product = relationship("Product")  # ❌ back_populates desactivado (no coincide con BD)
    company = relationship("Company")
    user = relationship("User", foreign_keys=[changed_by])

    def __repr__(self):
        return f"<ProductPriceHistory product={self.product_id} {self.price_usd_old}→{self.price_usd_new}>"


# ✅ SISTEMA ESCRITORIO: Departamento de productos
class Department(Base):
    __tablename__ = 'departments'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Código único
    name = Column(String(100), nullable=False)  # Nombre del departamento
    description = Column(String(200))  # Descripción opcional

    # Utilidad del departamento
    utility_percentage = Column(Float, default=30.0)  # Porcentaje de utilidad por defecto

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<Department {self.code} - {self.name}>"


# ✅ SISTEMA ESCRITORIO: Vendedores
class Seller(Base):
    __tablename__ = 'sellers'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Código único
    name = Column(String(100), nullable=False)  # Nombre del vendedor
    status = Column(String(2), default='01')  # 01=Activo, 02=Inactivo

    # Comisiones
    percent_sales = Column(Float, default=0.0)  # Porcentaje de comisión en ventas
    percent_receivable = Column(Float, default=0.0)  # Porcentaje de comisión en cobros

    # Usuario asociado (opcional)
    user_code = Column(String(60), ForeignKey('users.username'), nullable=True)

    # Comisiones gerenciales
    percent_gerencial_debit_note = Column(Float, default=0.0)
    percent_gerencial_credit_note = Column(Float, default=0.0)
    percent_returned_check = Column(Float, default=0.0)

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<Seller {self.code} - {self.name}>"


# ✅ SISTEMA ESCRITORIO: Grupos de clientes
class ClientGroup(Base):
    __tablename__ = 'client_groups'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Código único
    name = Column(String(100), nullable=False)  # Nombre del grupo
    description = Column(String(200))  # Descripción opcional

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<ClientGroup {self.code} - {self.name}>"


# ✅ SISTEMA ESCRITORIO: Áreas de ventas
class AreasSales(Base):
    __tablename__ = 'areas_sales'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    code = Column(String(10), nullable=False, unique=True, index=True)  # Código único
    name = Column(String(100), nullable=False)  # Nombre del área
    description = Column(String(200))  # Descripción opcional

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")

    def __repr__(self):
        return f"<AreasSales {self.code} - {self.name}>"


# ✅ SISTEMA ESCRITORIO: Tipos de impuestos (Categorías)
class TaxType(Base):
    __tablename__ = 'tax_types'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    code = Column(String(10), nullable=False)  # ✅ Código: 1=General, 2=Reducida, 3=Gen+Adic, 4=Exento, etc. (VARCHAR for backward compatibility)
    description = Column(String(100), nullable=False)  # "General", "Reducida", "Exento", etc.
    fiscal_printer_position = Column(Integer, nullable=True)  # ✅ Posición en impresora fiscal

    # ✅ OLD FIELDS (kept for backward compatibility, will be deprecated)
    name = Column(String(100), nullable=True)  # Deprecated: use description
    aliquot = Column(Float, nullable=True)  # Deprecated: moved to Tax model

    # Metadatos
    status = Column(Boolean, default=True)  # ✅ Estado activo
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")
    taxes = relationship("Tax", back_populates="tax_type")  # ✅ Relación con Tax

    def __repr__(self):
        return f"<TaxType {self.code} - {self.description}>"


# ✅ SISTEMA ESCRITORIO: Impuestos (Códigos específicos)
class Tax(Base):
    """
    Códigos de impuesto individuales (Venezuela).

    Relación con TaxType:
    - tax_type_id=1 (General): 01=16%
    - tax_type_id=2 (Reducida): 03=8%
    - tax_type_id=3 (General+Adicional): 02=31%
    - tax_type_id=4 (Exento): EX=0%
    - tax_type_id=7 (Percibido): 06=0%
    """
    __tablename__ = 'taxes'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # ✅ Código único de impuesto (01, 02, 03, EX, 06, etc.)
    code = Column(String(10), nullable=False, unique=True, index=True)

    description = Column(String(100), nullable=False)  # "Alicuota General", "Exento", etc.
    short_description = Column(String(50), nullable=False)  # "16%", "Exento", "8%", etc.
    aliquot = Column(Float, nullable=False)  # 16, 8, 31, 0

    # ✅ Relación con TaxType (categoría)
    tax_type_id = Column(Integer, ForeignKey('tax_types.id'), nullable=False)  # ✅ FK to tax_types

    status = Column(Boolean, default=True)  # ✅ Estado activo

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    # Relaciones
    company = relationship("Company")
    tax_type = relationship("TaxType", back_populates="taxes")

    def __repr__(self):
        return f"<Tax {self.code} - {self.description} ({self.aliquot}%)>"


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


# ==================== SISTEMA ESCRITORIO: OPERACIONES DE VENTA ====================

# ✅ SISTEMA ESCRITORIO: Operación de venta (tabla principal)
class SalesOperation(Base):
    __tablename__ = 'sales_operations'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    # ✅ Identificación
    correlative = Column(Integer, nullable=False)  # Correlativo interno
    operation_type = Column(String(20), nullable=False)  # BUDGET, ORDER, DELIVERYNOTE, BILL, CREDITNOTE, DEBITNOTE
    document_no = Column(String(50))  # Número de documento
    document_no_internal = Column(String(50), default='')  # Número interno
    control_no = Column(String(50))  # Número de control (para facturas)

    # ✅ Fechas
    emission_date = Column(DateTime, nullable=False)  # Fecha de emisión YYYY-MM-DD
    register_date = Column(DateTime, nullable=False)  # Fecha del servidor YYYY-MM-DD
    register_hour = Column(String(12))  # Hora de registro HH-MM-SS-MS
    expiration_date = Column(DateTime)  # Fecha de vencimiento

    # ✅ Cliente (información duplicada para historial)
    client_id = Column(Integer, ForeignKey('customers.id'), nullable=False)
    client_name = Column(String(150))  # Razón social (duplicado)
    client_tax_id = Column(String(20))  # RIF (duplicado)
    client_address = Column(String(300))  # Dirección (duplicado)
    client_phone = Column(String(20))  # Teléfono (duplicado)
    client_name_fiscal = Column(Integer, default=1)  # Tipo contribuyente (duplicado)

    # ✅ Vendedor y ubicaciones
    seller = Column(String(10), default='00')  # Código vendedor
    store = Column(String(10), default='00')  # Depósito
    locations = Column(String(10), default='00')  # Ubicación
    user_code = Column(String(60))  # Usuario
    station = Column(String(10), default='00')  # Estación de trabajo

    # ✅ Estado
    wait = Column(Boolean, default=False)  # Documento en espera
    pending = Column(Boolean, default=True)  # Documento pendiente
    canceled = Column(Boolean, default=False)  # Cancelado/anulado
    delivered = Column(Boolean, default=False)  # Entregado
    begin_used = Column(Boolean, default=False)  # Comenzar a usar

    # ✅ Totales del documento (sin impuestos incluidos en algunos campos)
    total_amount = Column(Float, default=0)  # Total cantidad de items
    total_net_details = Column(Float, default=0)  # Total detalles sin impuesto
    total_tax_details = Column(Float, default=0)  # Total impuestos de detalles
    total_details = Column(Float, default=0)  # Total detalles con descuento

    # ✅ Descuentos y fletes
    percent_discount = Column(Float, default=0)  # Porcentaje de descuento
    discount = Column(Float, default=0)  # Total descuento
    percent_freight = Column(Float, default=0)  # Porcentaje de flete
    freight = Column(Float, default=0)  # Total flete

    # ✅ Totales con impuestos
    total_net = Column(Float, default=0)  # Total neto sin impuestos
    total_tax = Column(Float, default=0)  # Total impuestos
    total = Column(Float, default=0)  # Total con impuestos

    # ✅ Pagos
    credit = Column(Float, default=0)  # Crédito
    cash = Column(Float, default=0)  # Contado

    # ✅ Costos
    total_net_cost = Column(Float, default=0)  # Total costo neto sin impuestos
    total_tax_cost = Column(Float, default=0)  # Total impuesto costo
    total_cost = Column(Float, default=0)  # Total costo con impuesto

    # ✅ Tipo de precio
    type_price = Column(Integer, default=0)  # 0=Max, 1=Oferta, 2=Mayor, 3=Min, 4=Variable

    # ✅ Contador de renglones
    total_count_details = Column(Float, default=0)  # Total de renglones (filas)

    # ✅ Impuestos de flete
    freight_tax = Column(String(2), default='01')  # 01=16%, 02=31%, 03=8%, 06=Percibido, EX=Exento
    freight_aliquot = Column(Float, default=16)  # Alicuota de impuesto

    # ✅ Retenciones
    total_retention_tax = Column(Float, default=0)  # Total retención IVA
    total_retention_municipal = Column(Float, default=0)  # Total retención municipal
    total_retention_islr = Column(Float, default=0)  # Total retención ISLR
    retention_tax_prorration = Column(Float, default=0)  # Porrateo retención IVA
    retention_islr_prorration = Column(Float, default=0)  # Porrateo retención ISLR
    retention_municipal_prorration = Column(Float, default=0)  # Porrateo retención municipal

    # ✅ Total de operación
    total_operation = Column(Float, default=0)  # Total de la operación

    # ✅ Impresora fiscal
    fiscal_impresion = Column(Boolean, default=False)  # Impreso por impresora fiscal
    fiscal_printer_serial = Column(String(50), default='')  # Serial de impresora fiscal
    fiscal_printer_z = Column(String(50), default='')  # Reporte Z
    fiscal_printer_date = Column(DateTime)  # Fecha de impresora fiscal

    # ✅ Moneda
    coin_code = Column(String(2), default='01')  # Código de moneda

    # ✅ Origen
    sale_point = Column(Boolean, default=False)  # Emitido desde PDV
    restorant = Column(Boolean, default=False)  # Emitido desde módulo restaurante

    # ✅ Datos de envío
    address_send = Column(String(300), default='')  # Dirección de envío
    contact_send = Column(String(100), default='')  # Contacto de envío
    phone_send = Column(String(20), default='')  # Teléfono de envío
    total_weight = Column(Float, default=0)  # Peso total

    # ✅ IGTF
    free_tax = Column(Boolean, default=False)  # Impuesto libre
    total_exempt = Column(Float, default=0)  # Total exento
    base_igtf = Column(Float, default=0)  # Base IGTF
    percent_igtf = Column(Float, default=0)  # Porcentaje IGTF
    igtf = Column(Float, default=0)  # Monto IGTF

    # ✅ Orden de compra relacionada
    shopping_order_document_no = Column(String(50), default='')  # Número orden de compra
    shopping_order_date = Column(DateTime)  # Fecha orden de compra

    # ✅ Comentarios
    operation_comments = Column(Text)  # Comentarios de la operación
    description = Column(Text)  # Descripción del documento

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    client = relationship("Customer")
    coins = relationship("SalesOperationCoin", cascade="all, delete-orphan", back_populates="sales_operation")
    details = relationship("SalesOperationDetail", cascade="all, delete-orphan", back_populates="sales_operation")
    taxes = relationship("SalesOperationTax", cascade="all, delete-orphan", back_populates="sales_operation")

    def __repr__(self):
        return f"<SalesOperation {self.operation_type} {self.document_no}>"


# ✅ SISTEMA ESCRITORIO: Montos en diferentes monedas
class SalesOperationCoin(Base):
    __tablename__ = 'sales_operation_coins'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    sales_operation_id = Column(Integer, ForeignKey('sales_operations.id'), nullable=False)

    # ✅ Identificación
    main_correlative = Column(Integer, nullable=False)  # Correlativo hacia sales_operations
    coin_code = Column(String(3), nullable=False)  # ✅ Código de moneda (USD, VES, etc.)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)  # ✅ FK a sistema multimoneda

    # ✅ Factor y tasas
    factor_type = Column(Integer, nullable=False)  # Tipo de factor (0 para moneda principal)
    buy_aliquot = Column(Float, nullable=False)  # Tasa de compra
    sales_aliquot = Column(Float, nullable=False)  # Tasa de venta

    # ✅ Montos del detalle (sin impuestos)
    total_net_details = Column(Float, default=0)
    total_tax_details = Column(Float, default=0)
    total_details = Column(Float, default=0)

    # ✅ Descuentos y fletes
    discount = Column(Float, default=0)
    freight = Column(Float, default=0)

    # ✅ Totales
    total_net = Column(Float, default=0)
    total_tax = Column(Float, default=0)
    total = Column(Float, default=0)

    # ✅ Pagos
    credit = Column(Float, default=0)
    cash = Column(Float, default=0)

    # ✅ Costos
    total_net_cost = Column(Float, default=0)
    total_tax_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)

    # ✅ Total operación
    total_operation = Column(Float, default=0)

    # ✅ Retenciones
    total_retention_tax = Column(Float, default=0)
    total_retention_municipal = Column(Float, default=0)
    total_retention_islr = Column(Float, default=0)
    retention_tax_prorration = Column(Float, default=0)
    retention_islr_prorration = Column(Float, default=0)
    retention_municipal_prorration = Column(Float, default=0)

    # ✅ IGTF
    total_exempt = Column(Float, default=0)

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    sales_operation = relationship("SalesOperation", back_populates="coins")
    currency = relationship("Currency", foreign_keys=[currency_id])  # ✅ Relación con sistema multimoneda

    def __repr__(self):
        return f"<SalesOperationCoin op={self.sales_operation_id} coin={self.coin_code}>"


# ✅ SISTEMA ESCRITORIO: Detalles de la operación (líneas)
class SalesOperationDetail(Base):
    __tablename__ = 'sales_operation_details'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    sales_operation_id = Column(Integer, ForeignKey('sales_operations.id'), nullable=False)

    # ✅ Identificación
    main_correlative = Column(Integer, nullable=False)  # Correlativo hacia sales_operations
    line = Column(Integer, nullable=False)  # Número de línea (secuencia)

    # ✅ Producto (información duplicada para historial)
    code_product = Column(String(50))  # Código del producto
    description_product = Column(String(200))  # Descripción del producto
    referenc = Column(String(50))  # Referencia del producto
    mark = Column(String(50))  # Marca del producto
    model = Column(String(50))  # Modelo del producto

    # ✅ Ubicación
    store = Column(String(10))  # Depósito
    locations = Column(String(10))  # Ubicación

    # ✅ Unidad
    unit = Column(Integer)  # Código de unidad (references PRODUCTS_UNITS)
    conversion_factor = Column(Float, default=0)  # Factor de conversión
    unit_type = Column(Integer, default=0)  # Tipo de unidad

    # ✅ Cantidades y precios
    amount = Column(Float, default=0)  # Cantidad de producto
    unitary_cost = Column(Float, default=0)  # Costo unitario
    sale_tax = Column(String(2), default='01')  # Código impuesto venta
    sale_aliquot = Column(Float, default=0)  # Alicuota de impuesto
    price = Column(Float, default=0)  # Precio sin impuesto
    type_price = Column(Integer, default=0)  # Tipo de precio

    # ✅ Costos
    total_net_cost = Column(Float, default=0)  # Total neto costo sin impuesto
    total_tax_cost = Column(Float, default=0)  # Total impuesto costo
    total_cost = Column(Float, default=0)  # Total costo con impuesto

    # ✅ Precios brutos
    total_net_gross = Column(Float, default=0)  # Total bruto sin impuesto
    total_tax_gross = Column(Float, default=0)  # Total impuesto bruto
    total_gross = Column(Float, default=0)  # Total con impuesto

    # ✅ Descuentos
    percent_discount = Column(Float, default=0)  # Porcentaje de descuento
    discount = Column(Float, default=0)  # Total descuento

    # ✅ Totales netos
    total_net = Column(Float, default=0)  # Total neto sin impuesto
    total_tax = Column(Float, default=0)  # Total impuestos
    total = Column(Float, default=0)  # Total con impuesto

    # ✅ Pendiente
    pending_amount = Column(Float, default=0)  # Cantidad pendiente

    # ✅ Impuesto de compra
    buy_tax = Column(String(2), default='01')  # Código impuesto compra
    buy_aliquot = Column(Float, default=0)  # Alicuota de impuesto

    # ✅ Inventario
    update_inventory = Column(Boolean, default=False)  # Hay movimiento de inventario

    # ✅ Cantidades para load orders
    amount_released_by_load_order = Column(Float, default=0)  # Cantidad liberada por orden de carga
    amount_discharged_by_load_delivery_note = Column(Float, default=0)  # Cantidad descontada por nota de entrega

    # ✅ Detalles adicionales
    product_type = Column(String(1))  # Tipo de producto
    description = Column(Text)  # Detalle de producto
    technician = Column(String(10), default='00')  # Técnico
    coin_code = Column(String(2), default='01')  # Código de moneda
    total_weight = Column(Float, default=0)  # Peso total

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    sales_operation = relationship("SalesOperation", back_populates="details")
    coins = relationship("SalesOperationDetailCoin", cascade="all, delete-orphan", back_populates="sales_operation_detail")

    def __repr__(self):
        return f"<SalesOperationDetail line={self.line} product={self.code_product}>"


# ✅ SISTEMA ESCRITORIO: Montos de detalles en diferentes monedas
class SalesOperationDetailCoin(Base):
    __tablename__ = 'sales_operation_detail_coins'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    sales_operation_detail_id = Column(Integer, ForeignKey('sales_operation_details.id'), nullable=True)

    # ✅ Identificación
    main_correlative = Column(Integer, nullable=False)  # Correlativo hacia sales_operations
    main_line = Column(Integer, nullable=False)  # Línea hacia sales_operation_details
    coin_code = Column(String(3), nullable=False)  # ✅ Código de moneda (USD, VES, etc.)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)  # ✅ FK a sistema multimoneda

    # ✅ Costos
    unitary_cost = Column(Float, default=0)
    total_net_cost = Column(Float, default=0)
    total_tax_cost = Column(Float, default=0)
    total_cost = Column(Float, default=0)

    # ✅ Precios brutos
    total_net_gross = Column(Float, default=0)
    total_tax_gross = Column(Float, default=0)
    total_gross = Column(Float, default=0)

    # ✅ Descuento
    discount = Column(Float, default=0)

    # ✅ Totales
    total_net = Column(Float, default=0)
    total_tax = Column(Float, default=0)
    total = Column(Float, default=0)

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    sales_operation_detail = relationship("SalesOperationDetail", back_populates="coins")
    currency = relationship("Currency", foreign_keys=[currency_id])  # ✅ Relación con sistema multimoneda

    def __repr__(self):
        return f"<SalesOperationDetailCoin line={self.main_line} coin={self.coin_code}>"


# ✅ SISTEMA ESCRITORIO: Impuestos del documento
class SalesOperationTax(Base):
    __tablename__ = 'sales_operation_taxes'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    sales_operation_id = Column(Integer, ForeignKey('sales_operations.id'), nullable=False)

    # ✅ Identificación
    main_correlative = Column(Integer, nullable=False)  # Correlativo hacia sales_operations
    line = Column(Integer, nullable=False)  # Línea
    taxe_code = Column(String(10), nullable=False)  # Código de impuesto
    aliquot = Column(Float, nullable=False)  # Alicuota (16, 8, 0, etc)

    # ✅ Montos
    taxable = Column(Float, default=0)  # Base imponible
    tax = Column(Float, default=0)  # Monto de impuesto

    # ✅ Tipo de impuesto
    tax_type = Column(Integer, nullable=False)  # Tipo de impuesto (references TAX_TYPE)

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    sales_operation = relationship("SalesOperation", back_populates="taxes")
    coins = relationship("SalesOperationTaxCoin", cascade="all, delete-orphan", back_populates="sales_operation_tax")

    def __repr__(self):
        return f"<SalesOperationTax tax={self.taxe_code} aliquot={self.aliquot}%>"


# ✅ SISTEMA ESCRITORIO: Impuestos en diferentes monedas
class SalesOperationTaxCoin(Base):
    __tablename__ = 'sales_operation_tax_coins'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    sales_operation_tax_id = Column(Integer, ForeignKey('sales_operation_taxes.id'), nullable=True)

    # ✅ Identificación
    main_correlative = Column(Integer, nullable=False)  # Correlativo hacia sales_operations
    main_taxe_code = Column(String(10), nullable=False)  # Código de impuesto
    main_line = Column(Integer, nullable=False)  # Línea hacia sales_operation_taxes
    coin_code = Column(String(3), nullable=False)  # ✅ Código de moneda (USD, VES, etc.)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=True)  # ✅ FK a sistema multimoneda

    # ✅ Montos
    taxable = Column(Float, default=0)  # Base imponible
    tax = Column(Float, default=0)  # Impuesto

    # Metadatos
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relaciones
    company = relationship("Company")
    sales_operation_tax = relationship("SalesOperationTax", back_populates="coins")
    currency = relationship("Currency", foreign_keys=[currency_id])  # ✅ Relación con sistema multimoneda

    def __repr__(self):
        return f"<SalesOperationTaxCoin tax={self.main_taxe_code} coin={self.coin_code}>"


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


# ================= AUDITORÍA Y SEGURIDAD =================
class AuditLog(Base):
    """Tabla de auditoría para seguimiento de seguridad"""
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    username = Column(String(100), nullable=True, index=True)
    action_type = Column(String(50), nullable=False, index=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    ip_address = Column(String(45), nullable=True, index=True)
    user_agent = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), index=True)

    # Relaciones
    company = relationship("Company")
    user = relationship("User")

    def __repr__(self):
        return f"<AuditLog {self.id}: {self.username} - {self.action_type} on {self.entity_type}>"