"""
Modelo de Tasas Diarias de Cambio
Sistema escalable para registrar tasas históricas BCV y manuales
"""

from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Date, ForeignKey, Index, UniqueConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from database import Base


class DailyRate(Base):
    """
    Tasas de cambio diarias para conversión de monedas.

    Almacena el historial completo de tasas BCV y manuales,
    permitiendo auditoría completa y trazabilidad.

    Ejemplo:
        - Fecha: 2025-01-17
        - Moneda base: VES (Bolívar)
        - Moneda destino: USD (Dólar)
        - Tasa: 34.50 (1 USD = 34.50 VES)
        - Fuente: BCV
    """
    __tablename__ = 'daily_rates'

    id = Column(Integer, primary_key=True, index=True)

    # Empresa y monedas
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False, index=True)
    base_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, index=True)
    target_currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False, index=True)

    # Tasa y fecha
    rate_date = Column(Date, nullable=False, index=True)
    exchange_rate = Column(Float, nullable=False)  # Tasa: 34.50 Bs/USD

    # Metadatos
    source = Column(String(50), nullable=False, default='MANUAL')  # BCV, MANUAL, SCHEDULED, API_BINANCE, API_FIXER
    is_active = Column(Boolean, default=True, nullable=False)

    # Auditoría
    created_at = Column(DateTime, default=func.now(), nullable=False)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    updated_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    # Notas
    notes = Column(String(500), nullable=True)
    meta_data = Column(String(1000), nullable=True)  # JSON para info extra

    # Relaciones
    company = relationship("Company", back_populates="daily_rates")
    base_currency = relationship("Currency", foreign_keys=[base_currency_id])
    target_currency = relationship("Currency", foreign_keys=[target_currency_id])
    creator = relationship("User", foreign_keys=[created_by])
    updater = relationship("User", foreign_keys=[updated_by])

    # Índices para búsquedas eficientes
    __table_args__ = (
        Index('idx_daily_rate_company_date', 'company_id', 'rate_date'),
        Index('idx_daily_rate_currencies', 'base_currency_id', 'target_currency_id'),
        Index('idx_daily_rate_date', 'rate_date'),
        # Restricción única: una tasa por día, empresa y par de monedas
        UniqueConstraint('company_id', 'base_currency_id', 'target_currency_id', 'rate_date', name='uq_daily_rate_per_day'),
        {'schema': None}
    )

    def __repr__(self):
        return f"<DailyRate(date={self.rate_date}, {self.base_currency.code}→{self.target_currency.code}={self.exchange_rate}, source={self.source})>"

    @property
    def inverse_rate(self):
        """Tasa inversa para conversión (1 / rate)"""
        if self.exchange_rate and self.exchange_rate != 0:
            return 1.0 / self.exchange_rate
        return None

    def to_dict(self):
        """Convertir a diccionario para API responses"""
        from sqlalchemy.orm import class_mapper

        columns = [c.key for c in class_mapper(self.__class__).columns]
        return {c: getattr(self, c) for c in columns}
