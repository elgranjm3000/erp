"""
Modelos de Conciliación Bancaria Multimoneda
Cuentas bancarias, transacciones y conciliación
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Float, Numeric, Boolean, Text, Index
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime

from database import Base


class BankAccount(Base):
    """
    Cuentas bancarias en múltiples monedas.

    Una empresa puede tener cuentas en VES, USD, EUR, etc.
    """

    __tablename__ = 'bank_accounts'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, index=True)

    # Información de la cuenta
    account_number = Column(String(50), nullable=False, index=True)
    account_type = Column(String(20), nullable=False, default='corriente')  # 'corriente', 'ahorro'
    bank_name = Column(String(100), nullable=False)
    bank_code = Column(String(20), nullable=True)  # Código del banco

    # Saldo
    balance = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        default=Decimal("0.00"),
        comment="Saldo actual de la cuenta"
    )

    # Metadatos
    is_active = Column(Boolean, default=True, index=True)
    is_default = Column(Boolean, default=False, comment="Cuenta por defecto para la moneda")
    notes = Column(Text, nullable=True)

    # Timestamps
    balance_last_updated = Column(DateTime, default=datetime.now, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)

    # Usuario
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    company = relationship("Company")
    currency = relationship("Currency")
    transactions = relationship("BankTransaction", cascade="all, delete-orphan")

    # Índice único: número de cuenta por empresa
    __table_args__ = (
        Index('idx_bank_account_company_currency', 'company_id', 'currency_id'),
        Index('idx_bank_account_active', 'company_id', 'is_active'),
    )

    def __repr__(self):
        return f"<BankAccount {self.bank_name} - {self.account_number} ({self.currency.code})>"


class BankTransaction(Base):
    """
    Transacciones bancarias en múltiples monedas.

    Registra ingresos y egresos con su respectiva tasa de cambio.
    """

    __tablename__ = 'bank_transactions'

    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    bank_account_id = Column(Integer, ForeignKey('bank_accounts.id'), nullable=False, index=True)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, index=True)

    # Información de la transacción
    transaction_type = Column(
        String(20),
        nullable=False,
        index=True,
        comment="'debit', 'credit', 'transfer_in', 'transfer_out'"
    )
    amount = Column(
        Numeric(precision=20, scale=2),
        nullable=False,
        comment="Monto de la transacción"
    )

    # Información de tasa de cambio (si es en moneda extranjera)
    exchange_rate = Column(
        Numeric(precision=20, scale=10),
        nullable=True,
        comment="Tasa de cambio usada (para moneda extranjera)"
    )
    exchange_rate_date = Column(
        DateTime,
        nullable=True,
        comment="Fecha de la tasa de cambio"
    )
    base_currency_amount = Column(
        Numeric(precision=20, scale=2),
        nullable=True,
        comment="Monto convertido a moneda base de la empresa"
    )

    # Descripción y referencia
    description = Column(String(500), nullable=False)
    reference_number = Column(String(100), nullable=True, index=True)
    transaction_date = Column(DateTime, nullable=False, index=True)

    # Conciliación
    related_invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True, index=True)
    related_purchase_id = Column(Integer, ForeignKey('purchases.id'), nullable=True, index=True)
    is_reconciled = Column(Boolean, default=False, index=True)
    reconciliation_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    recorded_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Relationships
    bank_account = relationship("BankAccount")
    currency = relationship("Currency")
    related_invoice = relationship("Invoice")
    related_purchase = relationship("Purchase")

    __table_args__ = (
        Index('idx_bank_transaction_account_date', 'bank_account_id', 'transaction_date'),
        Index('idx_bank_transaction_reconciled', 'company_id', 'is_reconciled'),
    )

    def __repr__(self):
        return f"<BankTransaction {self.transaction_type} {self.amount} {self.currency.code}>"
