"""
Currency Conversion Service
Servicio agnóstico de conversión de monedas con caché
"""

import logging
from typing import Optional, Dict, Tuple, Union
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from dataclasses import dataclass

from core.exchange_rate_providers import ExchangeRateManager, ExchangeRateProviderError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ConversionResult:
    """
    Resultado inmutable de una conversión de moneda.

    Attributes:
        original_amount: Monto original
        original_currency: Moneda origen
        converted_amount: Monto convertido
        target_currency: Moneda destino
        rate_used: Tasa utilizada
        converted_at: Timestamp de conversión
        provider: Proveedor que dio la tasa
    """
    original_amount: Decimal
    original_currency: str
    converted_amount: Decimal
    target_currency: str
    rate_used: Decimal
    converted_at: datetime
    provider: str

    def to_dict(self) -> dict:
        """Convierte a diccionario para serialización"""
        return {
            "original_amount": str(self.original_amount),
            "original_currency": self.original_currency,
            "converted_amount": str(self.converted_amount),
            "target_currency": self.target_currency,
            "rate_used": str(self.rate_used),
            "converted_at": self.converted_at.isoformat(),
            "provider": self.provider
        }


@dataclass(frozen=True)
class CurrencyAmount:
    """
    Representa un monto en una moneda específica.

    Lógica de precios agnóstica: no hay "precio en dólares",
    solo montos con su moneda correspondiente.
    """
    amount: Decimal
    currency: str

    def __post_init__(self):
        """Valida que el monto sea positivo"""
        if self.amount < 0:
            raise ValueError("Amount must be non-negative")

    def convert_to(
        self,
        target_currency: str,
        rate_manager: ExchangeRateManager,
        date: Optional[datetime] = None
    ) -> "CurrencyAmount":
        """
        Convierte este monto a otra moneda.

        Args:
            target_currency: Moneda destino
            rate_manager: Manager de tasas
            date: Fecha opcional para tasa histórica

        Returns:
            CurrencyAmount: Nuevo monto en moneda destino
        """
        result = CurrencyConversionService.convert(
            amount=self.amount,
            from_currency=self.currency,
            to_currency=target_currency,
            rate_manager=rate_manager,
            date=date
        )
        return CurrencyAmount(result.converted_amount, result.target_currency)

    def __str__(self) -> str:
        """Representación legible"""
        return f"{self.amount} {self.currency}"

    def __repr__(self) -> str:
        return f"CurrencyAmount(amount={self.amount}, currency='{self.currency}')"


class CurrencyConversionService:
    """
    Servicio de conversión de monedas con caché inteligente.

    Características:
    - Lógica agnóstica de monedas
    - Caché LRU para tasas frecuentes
    - Precisión Decimal para cálculos financieros
    - Inmutabilidad de resultados
    - Logging de auditoría
    """

    # Cache LRU en memoria (en prod usar Redis)
    _cache: Dict[Tuple[str, str, datetime], Decimal] = {}
    _cache_timestamps: Dict[Tuple[str, str, datetime], datetime] = {}
    _cache_ttl: timedelta = timedelta(minutes=5)

    # Contador de hits/miss para métricas
    _cache_hits: int = 0
    _cache_misses: int = 0

    @classmethod
    def convert(
        cls,
        amount: Union[Decimal, float, str],
        from_currency: str,
        to_currency: str,
        rate_manager: ExchangeRateManager,
        date: Optional[datetime] = None
    ) -> ConversionResult:
        """
        Convierte un monto entre monedas.

        Args:
            amount: Monto a convertir (Decimal, float o str)
            from_currency: Moneda origen (código ISO, ej: 'USD', 'VES')
            to_currency: Moneda destino
            rate_manager: Manager de tasas de cambio
            date: Fecha opcional para tasa histórica

        Returns:
            ConversionResult: Resultado inmutable de la conversión

        Raises:
            ValueError: Si el monto es inválido
            ExchangeRateProviderError: Si no se puede obtener la tasa
        """
        # Normalizar inputs
        try:
            amount_decimal = Decimal(str(amount))
        except (InvalidOperation, ValueError) as e:
            raise ValueError(f"Invalid amount '{amount}': {e}")

        from_currency = from_currency.upper().strip()
        to_currency = to_currency.upper().strip()

        if amount_decimal < 0:
            raise ValueError("Amount must be non-negative")

        # Misma moneda, sin conversión
        if from_currency == to_currency:
            logger.debug(f"No conversion needed: {amount} {from_currency}")
            return ConversionResult(
                original_amount=amount_decimal,
                original_currency=from_currency,
                converted_amount=amount_decimal,
                target_currency=to_currency,
                rate_used=Decimal("1"),
                converted_at=datetime.now(),
                provider="direct"
            )

        # Buscar en caché
        cache_key = cls._get_cache_key(from_currency, to_currency, date)
        cached_rate = cls._get_from_cache(cache_key)

        if cached_rate is not None:
            rate = cached_rate
            provider = "cache"
            logger.debug(f"Cache HIT for {from_currency}->{to_currency}")
        else:
            # Obtener tasa del manager
            logger.debug(f"Cache MISS for {from_currency}->{to_currency}, fetching from provider")
            rate = rate_manager.get_rate(from_currency, to_currency, date)

            if rate is None:
                raise ExchangeRateProviderError(
                    f"No exchange rate available for {from_currency} -> {to_currency}"
                )

            # Guardar en caché
            cls._save_to_cache(cache_key, rate)
            provider = "provider"

        # Calcular conversión
        converted_amount = amount_decimal * rate

        # Redondear a 2 decimales (precisión financiera estándar)
        converted_amount = converted_amount.quantize(Decimal("0.01"))

        result = ConversionResult(
            original_amount=amount_decimal,
            original_currency=from_currency,
            converted_amount=converted_amount,
            target_currency=to_currency,
            rate_used=rate,
            converted_at=datetime.now(),
            provider=provider
        )

        logger.info(
            f"Converted {amount_decimal} {from_currency} -> "
            f"{converted_amount} {to_currency} (rate: {rate}, provider: {provider})"
        )

        return result

    @classmethod
    def convert_multiple(
        cls,
        amounts: list[Tuple[Decimal, str]],
        target_currency: str,
        rate_manager: ExchangeRateManager,
        date: Optional[datetime] = None
    ) -> list[ConversionResult]:
        """
        Convierte múltiples montos a una moneda objetivo.

        Args:
            amounts: Lista de tuplas (monto, moneda_origen)
            target_currency: Moneda destino común
            rate_manager: Manager de tasas
            date: Fecha opcional

        Returns:
            List[ConversionResult]: Resultados de conversión
        """
        results = []

        for amount, from_currency in amounts:
            result = cls.convert(
                amount=amount,
                from_currency=from_currency,
                to_currency=target_currency,
                rate_manager=rate_manager,
                date=date
            )
            results.append(result)

        return results

    @classmethod
    def get_rate(
        cls,
        from_currency: str,
        to_currency: str,
        rate_manager: ExchangeRateManager,
        date: Optional[datetime] = None
    ) -> Decimal:
        """
        Obtiene solo la tasa de cambio (sin convertir monto).

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            rate_manager: Manager de tasas
            date: Fecha opcional

        Returns:
            Decimal: Tasa de cambio
        """
        result = cls.convert(
            amount=Decimal("1"),
            from_currency=from_currency,
            to_currency=to_currency,
            rate_manager=rate_manager,
            date=date
        )
        return result.rate_used

    @classmethod
    def _get_cache_key(
        cls,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime]
    ) -> Tuple:
        """Genera clave de caché"""
        # Usar fecha si existe, sino 'current'
        date_key = date.date() if date else "current"
        return (from_currency, to_currency, date_key)

    @classmethod
    def _get_from_cache(cls, key: Tuple) -> Optional[Decimal]:
        """Obtiene tasa del caché si no ha expirado"""
        if key in cls._cache:
            timestamp = cls._cache_timestamps[key]

            if datetime.now() - timestamp < cls._cache_ttl:
                cls._cache_hits += 1
                return cls._cache[key]
            else:
                # Expiró, remover
                del cls._cache[key]
                del cls._cache_timestamps[key]

        cls._cache_misses += 1
        return None

    @classmethod
    def _save_to_cache(cls, key: Tuple, rate: Decimal):
        """Guarda tasa en caché"""
        cls._cache[key] = rate
        cls._cache_timestamps[key] = datetime.now()

        # Limpiar caché si crece demasiado (máx 100 entradas)
        if len(cls._cache) > 100:
            cls._cleanup_cache()

    @classmethod
    def _cleanup_cache(cls):
        """Limpia entradas expiradas del caché"""
        now = datetime.now()
        expired_keys = [
            k for k, ts in cls._cache_timestamps.items()
            if now - ts > cls._cache_ttl
        ]

        for key in expired_keys:
            del cls._cache[key]
            del cls._cache_timestamps[key]

        logger.info(f"Cleaned {len(expired_keys)} expired cache entries")

    @classmethod
    def clear_cache(cls):
        """Limpia todo el caché"""
        cls._cache.clear()
        cls._cache_timestamps.clear()
        logger.info("Cache cleared")

    @classmethod
    def get_cache_stats(cls) -> Dict[str, int]:
        """Retorna estadísticas del caché"""
        return {
            "size": len(cls._cache),
            "hits": cls._cache_hits,
            "misses": cls._cache_misses,
            "hit_rate": cls._cache_hits / max(1, cls._cache_hits + cls._cache_misses)
        }
