"""
Modelos de Datos - Configuración de Monedas con Lógica Contable Venezolana
Precisión financiera, auditoría completa y cumplimiento tributario
"""

from sqlalchemy import Column, Integer, String, Numeric, Boolean, DateTime, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from database import Base


class Currency(Base):
    """
    Tabla principal de monedas con configuración completa.

    Campos de alta precisión para cálculos financieros y lógica
    contable específica para Venezuela.
    """

    __tablename__ = "currencies"

    # Identificación
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # Código ISO 4217 (ej: USD, VES, EUR)
    code = Column(String(3), nullable=False, unique=True, index=True)

    # Nombre completo de la moneda
    name = Column(String(100), nullable=False)

    # Símbolo de impresión (ej: $, Bs, €)
    symbol = Column(String(10), nullable=False)

    # Tasa de cambio actual (PRECISIÓN FINANCIERA: hasta 10 decimales)
    exchange_rate = Column(
        Numeric(precision=20, scale=10),
        nullable=False,
        default=Decimal("1.0000000000"),
        comment="Tasa de cambio actual. Precisión: hasta 10 decimales"
    )

    # Configuración de decimales para display
    decimal_places = Column(
        Integer,
        nullable=False,
        default=2,
        comment="Decimales para mostrar precios (default: 2, máx: 10)"
    )

    # Moneda base de la empresa
    is_base_currency = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="Solo una moneda base por empresa"
    )

    # Estado activo
    is_active = Column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Moneda activa para transacciones"
    )

    # FACTOR DE CONVERSIÓN (Lógica venezolana)
    conversion_factor = Column(
        Numeric(precision=20, scale=10),
        nullable=True,
        comment="""
        Factor de conversión según tipo de moneda:
        - VES: NULL (moneda base, no aplica conversión)
        - Más fuerte que VES (USD, EUR): tasa VES/moneda
        - Más débil (COP): tasa moneda/USD
        """
    )

    conversion_method = Column(
        String(20),
        nullable=True,
        comment="'direct' (VES->moneda), 'inverse' (moneda->VES), 'via_usd' (via USD)"
    )

    # === ✅ SISTEMA ESCRITORIO: Campos adicionales del desktop ERP ===

    # Tipo de factor de conversión (desktop ERP compatibility)
    factor_type = Column(
        Integer,
        nullable=False,
        default=0,
        comment="""
        Tipo de factor según sistema desktop:
        - 0: Moneda base (no requiere conversión)
        - 1: Moneda convertida (requiere tasa de cambio)
        """
    )

    # Tipo de redondeo para cálculos
    rounding_type = Column(
        Integer,
        nullable=False,
        default=2,
        comment="""
        Tipo de redondeo:
        - 0: Sin redondeo
        - 1: Redondeo hacia arriba
        - 2: Redondeo estándar (4 hacia abajo, 5 hacia arriba)
        """
    )

    # Mostrar en listados (desktop ERP compatibility)
    show_in_browsers = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Mostrar esta moneda en los listados de selección"
    )

    # Usar para valoración de inventario
    value_inventory = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="¿Se usa esta moneda para valorar el inventario?"
    )

    # === OBLIGACIONES TRIBUTARIAS VENEZOLANAS ===

    # IGTF: Impuesto a Grandes Transacciones Financieras
    applies_igtf = Column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
        comment="""
        ¿Aplica IGTF para esta moneda?
        - True: USD, EUR (divisas)
        - False: VES (moneda nacional)
        """
    )

    # Tasa de IGTF para esta moneda (default 3%)
    igtf_rate = Column(
        Numeric(precision=5, scale=2),
        nullable=False,
        default=Decimal("3.00"),
        comment="Tasa de IGTF aplicable. Default: 3% (Ley de IGTF)"
    )

    # Exención especial de IGTF
    igtf_exempt = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Exención especial (ej: contribuyentes especiales)"
    )

    # Monto mínimo para IGTF (en moneda local equivalente)
    igtf_min_amount = Column(
        Numeric(precision=20, scale=2),
        nullable=True,
        comment="Monto mínimo en moneda local para aplicar IGTF"
    )

    # === MÉTODOS DE ACTUALIZACIÓN DE TASAS ===

    # Tipo de actualización
    rate_update_method = Column(
        String(20),
        nullable=False,
        default="manual",
        comment="'manual', 'api_bcv', 'api_binance', 'scraper', 'scheduled'"
    )

    # Última actualización
    last_rate_update = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="Timestamp de última actualización de tasa"
    )

    # Próxima actualización programada
    next_rate_update = Column(
        DateTime,
        nullable=True,
        comment="Timestamp de próxima actualización automática"
    )

    # URL de API o fuente para actualización automática
    rate_source_url = Column(
        String(500),
        nullable=True,
        comment="URL de API o fuente para scraping"
    )

    # === METADATOS Y AUDITORÍA ===

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Usuario que creó
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Usuario que actualizó por última vez
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Notas sobre la moneda
    notes = Column(Text, nullable=True)

    # Configuración adicional (JSON)
    config = Column(Text, nullable=True)

    # ==================== RELATIONSHIPS ====================
    company = relationship("Company", back_populates="currencies")
    coin_history = relationship("CoinHistory", cascade="all, delete-orphan")  # ✅ SISTEMA ESCRITORIO: Historial de monedas

    # ==================== ÍNDICES Y RESTRICCIONES ====================
    __table_args__ = (
        # Código único por empresa
        UniqueConstraint('company_id', 'code',
                       name='uq_currency_code_per_company'),

        # Índices compuestos
        Index('idx_currency_company_active', 'company_id', 'is_active'),
        Index('idx_currency_igtf', 'company_id', 'applies_igtf', 'is_active'),
        Index('idx_currency_base', 'company_id', 'is_base_currency'),
    )

    def __repr__(self):
        return (
            f"<Currency("
            f"code={self.code}, "
            f"symbol={self.symbol}, "
            f"rate={self.exchange_rate}, "
            f"base={self.is_base_currency}"
            f")>"
        )

    def to_dict(self):
        """Convierte a diccionario para API responses"""
        return {
            "id": self.id,
            "company_id": self.company_id,
            "code": self.code,
            "name": self.name,
            "symbol": self.symbol,
            "exchange_rate": float(self.exchange_rate) if self.exchange_rate else None,
            "decimal_places": self.decimal_places,
            "is_base_currency": self.is_base_currency,
            "is_active": self.is_active,
            "conversion_factor": float(self.conversion_factor) if self.conversion_factor else None,
            "conversion_method": self.conversion_method,
            # ✅ Desktop ERP fields
            "factor_type": self.factor_type,
            "rounding_type": self.rounding_type,
            "show_in_browsers": self.show_in_browsers,
            "value_inventory": self.value_inventory,
            "applies_igtf": self.applies_igtf,
            "igtf_rate": float(self.igtf_rate) if self.igtf_rate else None,
            "igtf_exempt": self.igtf_exempt,
            "igtf_min_amount": float(self.igtf_min_amount) if self.igtf_min_amount else None,
            "rate_update_method": self.rate_update_method,
            "last_rate_update": self.last_rate_update.isoformat() if self.last_rate_update else None,
            "next_rate_update": self.next_rate_update.isoformat() if self.next_rate_update else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }


class CurrencyRateHistory(Base):
    """
    Registro histórico de cambios de tasas de cambio.

    Cada cambio de tasa genera un registro inmutable para:
    - Auditoría completa
    - Reportes contables
    - Análisis de tendencias
    - Reconstrucción de estados históricos
    """

    __tablename__ = "currency_rate_history"

    id = Column(Integer, primary_key=True, index=True)

    # Referencia a moneda
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)

    # === CAMBIOS REGISTRADOS ===

    # Valor ANTERIOR de la tasa
    old_rate = Column(
        Numeric(precision=20, scale=10),
        nullable=False,
        comment="Valor de tasa antes del cambio"
    )

    # Valor NUEVO de la tasa
    new_rate = Column(
        Numeric(precision=20, scale=10),
        nullable=False,
        comment="Valor de tasa después del cambio"
    )

    # Diferencia (nuevo - antiguo)
    rate_difference = Column(
        Numeric(precision=20, scale=10),
        nullable=False,
        comment="Diferencia absoluta: new_rate - old_rate"
    )

    # Variación porcentual
    rate_variation_percent = Column(
        Numeric(precision=10, scale=4),
        nullable=True,
        comment="Variación porcentual: ((new - old) / old) * 100"
    )

    # === METADATA DEL CAMBIO ===

    # Usuario o proceso que realizó el cambio
    changed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Tipo de cambio
    change_type = Column(
        String(20),
        nullable=False,
        comment="'manual', 'automatic_api', 'scheduled', 'correction'"
    )

    # Fuente del cambio (API, scraper, usuario, etc.)
    change_source = Column(
        String(100),
        nullable=True,
        comment="'api_bcv', 'api_binance', 'user_admin', 'system_scheduled', etc."
    )

    # IP address del usuario
    user_ip = Column(String(45), nullable=True)

    # User agent
    user_agent = Column(String(500), nullable=True)

    # Razón del cambio (opcional)
    change_reason = Column(Text, nullable=True)

    # Datos adicionales del proveedor (JSON)
    provider_metadata = Column(Text, nullable=True)

    # === TIMESTAMP ===
    changed_at = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
        comment="Timestamp exacto del cambio"
    )

    # ==================== ÍNDICES ====================
    __table_args__ = (
        Index('idx_rate_history_currency_date', 'currency_id', 'changed_at'),
        Index('idx_rate_history_company_date', 'company_id', 'changed_at'),
    )

    def __repr__(self):
        return (
            f"<CurrencyRateHistory("
            f"currency_id={self.currency_id}, "
            f"old={self.old_rate}, "
            f"new={self.new_rate}, "
            f"date={self.changed_at}"
            f")>"
        )

    def to_dict(self):
        """Convierte a diccionario"""
        return {
            "id": self.id,
            "currency_id": self.currency_id,
            "company_id": self.company_id,
            "old_rate": float(self.old_rate),
            "new_rate": float(self.new_rate),
            "rate_difference": float(self.rate_difference),
            "rate_variation_percent": float(self.rate_variation_percent) if self.rate_variation_percent else None,
            "changed_by": self.changed_by,
            "change_type": self.change_type,
            "change_source": self.change_source,
            "changed_at": self.changed_at.isoformat(),
            "change_reason": self.change_reason
        }


class IGTFConfig(Base):
    """
    Configuración de IGTF (Impuesto a Grandes Transacciones Financieras).

    Almacena la configuración específica de IGTF por empresa y moneda,
    permitiendo gestión flexible de obligaciones tributarias.
    """

    __tablename__ = "igtf_config"

    id = Column(Integer, primary_key=True, index=True)

    # Referencias
    company_id = Column(Integer, ForeignKey("companies.id"), nullable=False, index=True)
    currency_id = Column(Integer, ForeignKey("currencies.id"), nullable=False, index=True)

    # === CONFIGURACIÓN DE IGTF ===

    # Si la empresa es contribuyente especial de IGTF
    is_special_contributor = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Contribuyente especial de IGTF (retiene 100% del impuesto)"
    )

    # Tasa de IGTF aplicable (default 3% según Ley)
    igtf_rate = Column(
        Numeric(precision=5, scale=2),
        nullable=False,
        default=Decimal("3.00"),
        comment="Tasa de IGTF. Default: 3%. Puede variar por ley"
    )

    # Monto mínimo en moneda LOCAL para aplicar IGTF
    min_amount_local = Column(
        Numeric(precision=20, scale=2),
        nullable=True,
        comment="Monto mínimo en moneda local equivalente"
    )

    # Monto mínimo en moneda EXTRANJERA para aplicar IGTF
    min_amount_foreign = Column(
        Numeric(precision=20, scale=2),
        nullable=True,
        comment="Monto mínimo en moneda extranjera"
    )

    # Exenciones específicas
    is_exempt = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Esta empresa está exenta de IGTF"
    )

    # Exención por tipo de transacción
    exempt_transactions = Column(
        Text,
        nullable=True,
        comment="JSON con tipos de transacción exentas"
    )

    # Métodos de pago que aplican IGTF
    applicable_payment_methods = Column(
        Text,
        nullable=True,
        comment="JSON: ['transfer', 'credit_card', 'debit_card']"
    )

    # === CONTROL DE VIGENCIA ===

    valid_from = Column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        comment="Inicio de vigencia de esta configuración"
    )

    valid_until = Column(
        DateTime,
        nullable=True,
        comment="Fin de vigencia (NULL = vigente)"
    )

    # === AUDITORÍA ===
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Notas
    notes = Column(Text, nullable=True)

    # ==================== ÍNDICES ====================
    __table_args__ = (
        UniqueConstraint('company_id', 'currency_id',
                       name='uq_igtf_config_per_currency'),
        Index('idx_igtf_company_active', 'company_id', 'valid_from', 'valid_until'),
    )

    def __repr__(self):
        return (
            f"<IGTFConfig("
            f"company_id={self.company_id}, "
            f"currency_id={self.currency_id}, "
            f"rate={self.igtf_rate}%, "
            f"special_contributor={self.is_special_contributor}"
            f")>"
        )

    def to_dict(self):
        """Convierte a diccionario para API responses"""
        import json
        return {
            "id": self.id,
            "company_id": self.company_id,
            "currency_id": self.currency_id,
            "is_special_contributor": self.is_special_contributor,
            "igtf_rate": float(self.igtf_rate) if self.igtf_rate else None,
            "min_amount_local": float(self.min_amount_local) if self.min_amount_local else None,
            "min_amount_foreign": float(self.min_amount_foreign) if self.min_amount_foreign else None,
            "is_exempt": self.is_exempt,
            "exempt_transactions": json.loads(self.exempt_transactions) if self.exempt_transactions else None,
            "applicable_payment_methods": json.loads(self.applicable_payment_methods) if self.applicable_payment_methods else None,
            "valid_from": self.valid_from.isoformat() if self.valid_from else None,
            "valid_until": self.valid_until.isoformat() if self.valid_until else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "notes": self.notes
        }
