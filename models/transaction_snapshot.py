"""
Transaction Snapshot Models
Modelos para inmutabilidad de transacciones y auditoría
"""

from sqlalchemy import Column, Integer, String, DateTime, Numeric, ForeignKey, Text, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal

from database import Base


class TransactionSnapshot(Base):
    """
    Snapshot inmutable de una transacción.

    Almacena el estado exacto de una transacción en el momento
    de su creación para auditoría y preservación histórica.

    Attributes:
        transaction_type: Tipo de transacción (invoice, purchase, etc.)
        transaction_id: ID de la transacción original
        amount_original: Monto en moneda de pago
        currency_original: Moneda de pago
        amount_base: Monto en moneda base
        currency_base: Moneda base
        exchange_rate: Tasa utilizada
        exchange_rate_date: Fecha de la tasa
        taxes_snapshot: Snapshot de impuestos calculados
        metadata: Metadatos adicionales (JSON)
        created_at: Timestamp de creación
        is_finalized: Si el snapshot es final (no editable)
    """

    __tablename__ = "transaction_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # Referencia a la transacción original
    transaction_type = Column(String(50), nullable=False)  # 'invoice', 'purchase', etc.
    transaction_id = Column(Integer, nullable=False)

    # Montos en diferentes monedas (SNAPSHOT - INMUTABLE)
    amount_original = Column(Numeric(precision=20, scale=4), nullable=False)
    currency_original = Column(String(3), nullable=False)  # ISO 4217

    amount_base = Column(Numeric(precision=20, scale=4), nullable=False)
    currency_base = Column(String(3), nullable=False)  # Moneda base de la empresa

    # Tasa de cambio utilizada (INMUTABLE)
    exchange_rate = Column(Numeric(precision=20, scale=6), nullable=False)
    exchange_rate_date = Column(DateTime, nullable=False)
    exchange_rate_provider = Column(String(50))  # 'bcv', 'binance', etc.

    # Snapshot de impuestos (INMUTABLE)
    taxes_snapshot = Column(JSON, nullable=True)
    """
    Estructura JSON:
    {
        "iva": {
            "rate": 16.0,
            "taxable_amount": 1000.00,
            "tax_amount": 160.00,
            "rule_id": "iva_estandar"
        },
        "igtf": {
            "rate": 3.0,
            "taxable_amount": 1160.00,
            "tax_amount": 34.80,
            "rule_id": "igtf_divisas"
        }
    }
    """

    # Metadatos adicionales
    transaction_metadata = Column(JSON, nullable=True)
    """
    Estructura JSON:
    {
        "customer_id": 123,
        "warehouse_id": 5,
        "items": [
            {
                "product_id": 10,
                "quantity": 2,
                "unit_price": 500.00,
                "currency": "USD",
                "taxes": {...}
            }
        ],
        "payment_method": "transfer",
        "user_id": 5
    }
    """

    # Control de inmutabilidad
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_finalized = Column(Boolean, default=True, nullable=False)

    # Auditoría
    created_by = Column(Integer, ForeignKey('users.id'))
    notes = Column(Text)

    def __repr__(self):
        return (
            f"<TransactionSnapshot("
            f"type={self.transaction_type}, "
            f"id={self.transaction_id}, "
            f"amount={self.amount_original} {self.currency_original}"
            f")>"
        )

    def to_dict(self) -> dict:
        """Convierte el snapshot a diccionario"""
        return {
            "id": self.id,
            "transaction_type": self.transaction_type,
            "transaction_id": self.transaction_id,
            "amount_original": {
                "amount": float(self.amount_original),
                "currency": self.currency_original
            },
            "amount_base": {
                "amount": float(self.amount_base),
                "currency": self.currency_base
            },
            "exchange_rate": {
                "rate": float(self.exchange_rate),
                "date": self.exchange_rate_date.isoformat() if self.exchange_rate_date else None,
                "provider": self.exchange_rate_provider
            },
            "taxes_snapshot": self.taxes_snapshot,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "is_finalized": self.is_finalized
        }


class TransactionAuditLog(Base):
    """
    Log de auditoría de transacciones.

    Registra TODOS los cambios y estados por los que pasa una transacción.
    """

    __tablename__ = "transaction_audit_log"

    id = Column(Integer, primary_key=True, index=True)

    # Referencia a transacción
    transaction_type = Column(String(50), nullable=False)
    transaction_id = Column(Integer, nullable=False)

    # Información del cambio
    action = Column(String(50), nullable=False)  # 'created', 'updated', 'cancelled', etc.
    previous_state = Column(JSON, nullable=True)
    new_state = Column(JSON, nullable=True)

    # Campos modificados
    changed_fields = Column(JSON, nullable=True)  # ['amount', 'status', ...]

    # Quién hizo el cambio
    user_id = Column(Integer, ForeignKey('users.id'))
    ip_address = Column(String(45))
    user_agent = Column(String(255))

    # Timestamp
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Razón del cambio
    reason = Column(Text)

    def __repr__(self):
        return (
            f"<TransactionAuditLog("
            f"type={self.transaction_type}, "
            f"id={self.transaction_id}, "
            f"action={self.action}, "
            f"timestamp={self.created_at}"
            f")>"
        )


class ExchangeRateSnapshot(Base):
    """
    Snapshot de tasas de cambio utilizadas en transacciones.

    Permite reconstruir exactamente qué tasas se usaron en cada momento.
    """

    __tablename__ = "exchange_rate_snapshots"

    id = Column(Integer, primary_key=True, index=True)

    # Tasa de cambio
    from_currency = Column(String(3), nullable=False)
    to_currency = Column(String(3), nullable=False)
    rate = Column(Numeric(precision=20, scale=6), nullable=False)

    # Metadata
    provider = Column(String(50), nullable=False)  # 'bcv', 'binance', etc.
    provider_rate_id = Column(String(100))  # ID de la tasa en el proveedor

    # Vigencia
    valid_from = Column(DateTime, nullable=False, default=datetime.utcnow)
    valid_until = Column(DateTime, nullable=True)  # NULL = vigente

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Auditoría
    created_by = Column(Integer, ForeignKey('users.id'))

    def __repr__(self):
        return (
            f"<ExchangeRateSnapshot("
            f"{self.from_currency}->{self.to_currency}={self.rate}, "
            f"provider={self.provider}"
            f")>"
        )
