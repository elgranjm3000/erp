"""
Servicio de Monedas Mejorado v2.0

Con caché, excepciones personalizadas y operaciones batch.
"""

from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from models import Currency, CurrencyRateHistory, Company
from schemas import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyRateUpdate,
)
from core.cache import cached_result, invalidate_caches
from core.exceptions import (
    CurrencyNotFoundError,
    DuplicateCurrencyError,
    InvalidCurrencyCodeError,
    InvalidExchangeRateError,
    BaseCurrencyAlreadyExistsError,
    CannotDeleteBaseCurrencyError,
    NotFoundError,
    ValidationError,
)


class CurrencyServiceV2:
    """
    Servicio mejorado para gestión de monedas con caché y mejor manejo de errores.
    """

    def __init__(self, db: Session):
        self.db = db
        self._cache_prefix = "currency"

    # ==================== CRUD MEJORADO ====================

    @cached_result(ttl=300, key_prefix="currency")
    def get_currency(self, currency_id: int, company_id: int) -> CurrencyResponse:
        """
        Obtiene moneda por ID con caché.

        Raises:
            CurrencyNotFoundError: Si no existe
        """
        currency = self.db.query(Currency).filter(
            and_(
                Currency.id == currency_id,
                Currency.company_id == company_id
            )
        ).first()

        if not currency:
            raise CurrencyNotFoundError(
                currency_code=str(currency_id),
                company_id=company_id
            )

        return CurrencyResponse.from_orm(currency)

    @cached_result(ttl=60, key_prefix="currencies_list")
    def list_currencies(
        self,
        company_id: int,
        is_active: Optional[bool] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[CurrencyResponse]:
        """
        Lista monedas con filtros y caché.
        """
        query = self.db.query(Currency).filter(Currency.company_id == company_id)

        if is_active is not None:
            query = query.filter(Currency.is_active == is_active)

        currencies = query.offset(skip).limit(limit).all()
        return [CurrencyResponse.from_orm(c) for c in currencies]

    def create_currency(self, currency_data: CurrencyCreate, company_id: int, user_id: int) -> CurrencyResponse:
        """
        Crea nueva moneda con validaciones mejoradas.

        Raises:
            DuplicateCurrencyError: Si ya existe
            InvalidCurrencyCodeError: Si el código es inválido
            BaseCurrencyAlreadyExistsError: Si ya hay moneda base
        """
        # Validar código ISO 4217
        if not self._is_valid_iso_code(currency_data.code):
            raise InvalidCurrencyCodeError(
                currency_code=currency_data.code,
                reason="Must be a valid ISO 4217 code (3 letters)"
            )

        # Verificar duplicado
        existing = self.db.query(Currency).filter(
            and_(
                Currency.company_id == company_id,
                Currency.code == currency_data.code.upper()
            )
        ).first()

        if existing:
            raise DuplicateCurrencyError(
                currency_code=currency_data.code,
                company_id=company_id
            )

        # Verificar moneda base única
        if currency_data.is_base_currency:
            existing_base = self.db.query(Currency).filter(
                and_(
                    Currency.company_id == company_id,
                    Currency.is_base_currency == True
                )
            ).first()

            if existing_base:
                raise BaseCurrencyAlreadyExistsError(
                    company_id=company_id,
                    existing_currency=existing_base.code
                )

        # Validar tasa de cambio
        try:
            rate = Decimal(str(currency_data.exchange_rate))
            if rate <= 0:
                raise InvalidExchangeRateError(
                    rate=currency_data.exchange_rate,
                    reason="Must be greater than 0"
                )
        except (ValueError, TypeError):
            raise InvalidExchangeRateError(
                rate=currency_data.exchange_rate,
                reason="Must be a valid decimal number"
            )

        # Crear moneda
        currency = Currency(
            company_id=company_id,
            code=currency_data.code.upper(),
            name=currency_data.name,
            symbol=currency_data.symbol,
            exchange_rate=rate,
            decimal_places=currency_data.decimal_places or 2,
            is_base_currency=currency_data.is_base_currency or False,
            conversion_method=currency_data.conversion_method or "direct",
            applies_igtf=currency_data.applies_igtf or False,
            igtf_rate=currency_data.igtf_rate or "3.00",
            igtf_exempt=currency_data.igtf_exempt or False,
            igtf_min_amount=currency_data.igtf_min_amount,
            rate_update_method=currency_data.rate_update_method or "manual",
            created_by=user_id,
        )

        # Calcular conversion factor
        if not currency.is_base_currency:
            currency.conversion_factor = self._calculate_conversion_factor(
                currency.exchange_rate,
                currency.conversion_method
            )

        self.db.add(currency)
        self.db.commit()
        self.db.refresh(currency)

        # Invalidar caché
        invalidate_caches(pattern=f"{self._cache_prefix}:list_currencies")

        return CurrencyResponse.from_orm(currency)

    def update_currency(
        self,
        currency_id: int,
        currency_data: CurrencyUpdate,
        company_id: int,
        user_id: int
    ) -> CurrencyResponse:
        """
        Actualiza moneda existente.
        """
        currency = self.db.query(Currency).filter(
            and_(
                Currency.id == currency_id,
                Currency.company_id == company_id
            )
        ).first()

        if not currency:
            raise CurrencyNotFoundError(
                currency_code=str(currency_id),
                company_id=company_id
            )

        # Actualizar campos
        update_data = currency_data.dict(exclude_unset=True)

        for field, value in update_data.items():
            if hasattr(currency, field):
                setattr(currency, field, value)

        currency.updated_by = user_id
        currency.updated_at = datetime.now()

        self.db.commit()
        self.db.refresh(currency)

        # Invalidar caché
        invalidate_caches(pattern=f"{self._cache_prefix}:get_currency:{currency_id}")
        invalidate_caches(pattern=f"{self._cache_prefix}:list_currencies")

        return CurrencyResponse.from_orm(currency)

    def delete_currency(self, currency_id: int, company_id: int) -> None:
        """
        Soft delete de moneda.

        Raises:
            CannotDeleteBaseCurrencyError: Si es moneda base
        """
        currency = self.db.query(Currency).filter(
            and_(
                Currency.id == currency_id,
                Currency.company_id == company_id
            )
        ).first()

        if not currency:
            raise CurrencyNotFoundError(
                currency_code=str(currency_id),
                company_id=company_id
            )

        if currency.is_base_currency:
            raise CannotDeleteBaseCurrencyError(currency_code=currency.code)

        currency.is_active = False
        currency.updated_at = datetime.now()

        self.db.commit()

        # Invalidar caché
        invalidate_caches(pattern=f"{self._cache_prefix}:get_currency:{currency_id}")
        invalidate_caches(pattern=f"{self._cache_prefix}:list_currencies")

    # ==================== BATCH OPERATIONS ====================

    def bulk_create_currencies(
        self,
        currencies_data: List[CurrencyCreate],
        company_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Crea múltiples monedas en batch.

        Returns:
            Dict con resultados: {
                "created": List[CurrencyResponse],
                "failed": List[dict],
                "total": int,
                "success_count": int,
                "error_count": int
            }
        """
        results = {
            "created": [],
            "failed": [],
            "total": len(currencies_data),
            "success_count": 0,
            "error_count": 0
        }

        for currency_data in currencies_data:
            try:
                currency = self.create_currency(currency_data, company_id, user_id)
                results["created"].append(currency)
                results["success_count"] += 1
            except Exception as e:
                results["failed"].append({
                    "currency_code": currency_data.code,
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                results["error_count"] += 1

        # Invalidar caché
        invalidate_caches(pattern=f"{self._cache_prefix}:list_currencies")

        return results

    def bulk_update_rates(
        self,
        updates: List[Dict[str, Any]],
        company_id: int,
        user_id: int
    ) -> Dict[str, Any]:
        """
        Actualiza múltiples tasas de cambio en batch.

        Args:
            updates: List de dicts con {currency_id, new_rate, change_reason}

        Returns:
            Dict con resultados
        """
        results = {
            "updated": [],
            "failed": [],
            "total": len(updates),
            "success_count": 0,
            "error_count": 0
        }

        for update_data in updates:
            try:
                currency_id = update_data["currency_id"]
                rate_update = CurrencyRateUpdate(
                    new_rate=update_data["new_rate"],
                    change_reason=update_data.get("change_reason"),
                    change_type=update_data.get("change_type", "manual"),
                    change_source=update_data.get("change_source", "bulk_update")
                )

                # Actualizar usando el servicio existente
                from services.currency_business_service import CurrencyBusinessLogic
                business_logic = CurrencyBusinessLogic(self.db)

                currency = business_logic.update_currency_rate(
                    currency_id=currency_id,
                    rate_update=rate_update,
                    company_id=company_id,
                    user_id=user_id
                )

                results["updated"].append({
                    "currency_id": currency_id,
                    "old_rate": str(update_data.get("old_rate", "N/A")),
                    "new_rate": str(rate_update.new_rate)
                })
                results["success_count"] += 1

            except Exception as e:
                results["failed"].append({
                    "currency_id": update_data.get("currency_id"),
                    "error": str(e),
                    "error_type": type(e).__name__
                })
                results["error_count"] += 1

        # Invalidar caché
        invalidate_caches(pattern=f"{self._cache_prefix}")

        return results

    # ==================== HELPERS ====================

    def _is_valid_iso_code(self, code: str) -> bool:
        """Valida que sea un código ISO 4217 válido."""
        if not code or len(code) != 3:
            return False

        # Lista de códigos comunes (puedes agregar más)
        common_codes = {
            'USD', 'EUR', 'GBP', 'JPY', 'VES', 'COP', 'ARS', 'MXN',
            'BRL', 'CLP', 'PEN', 'CAD', 'AUD', 'CHF', 'CNY', 'INR'
        }

        return code.upper() in common_codes or (len(code) == 3 and code.isalpha())

    def _calculate_conversion_factor(
        self,
        rate: Decimal,
        method: str
    ) -> Optional[Decimal]:
        """Calcula el factor de conversión."""
        if method == "direct":
            return Decimal("1") / rate if rate != 0 else None
        elif method == "inverse":
            return rate
        elif method == "via_usd":
            # Implementar lógica para triangulación
            return Decimal("1") / rate if rate != 0 else None
        return None


# Función helper para crear el servicio
def get_currency_service_v2(db: Session) -> CurrencyServiceV2:
    """Factory function para crear instancia del servicio."""
    return CurrencyServiceV2(db)
