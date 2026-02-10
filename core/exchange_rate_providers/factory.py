"""
Exchange Rate Provider Factory and Manager
Centraliza la gestión de múltiples proveedores de tasas
"""

import logging
from typing import Optional, Dict
from datetime import datetime
from decimal import Decimal

from .base import ExchangeRateProvider, ExchangeRateProviderError
from .bcv_provider import BCVProvider
from .binance_provider import BinanceProvider
from .mock_provider import MockProvider


logger = logging.getLogger(__name__)


class ExchangeRateProviderFactory:
    """
    Factory para crear instancias de proveedores de tasas.

    Permite cambiar fácilmente entre BCV, Binance, Mock, etc.
    """

    # Registry de proveedores disponibles
    _providers: Dict[str, type] = {
        "bcv": BCVProvider,
        "binance": BinanceProvider,
        "mock": MockProvider,
    }

    @classmethod
    def register_provider(cls, name: str, provider_class: type):
        """
        Registra un nuevo proveedor.

        Args:
            name: Nombre del proveedor
            provider_class: Clase del proveedor (debe heredar de ExchangeRateProvider)
        """
        if not issubclass(provider_class, ExchangeRateProvider):
            raise ValueError(f"{provider_class} must inherit from ExchangeRateProvider")

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered exchange rate provider: {name}")

    @classmethod
    def create(cls, provider_name: str, **kwargs) -> ExchangeRateProvider:
        """
        Crea una instancia de un proveedor.

        Args:
            provider_name: Nombre del proveedor ('bcv', 'binance', 'mock')
            **kwargs: Argumentos adicionales para el proveedor

        Returns:
            ExchangeRateProvider: Instancia del proveedor

        Raises:
            ValueError: Si el proveedor no existe
        """
        provider_name_lower = provider_name.lower()

        if provider_name_lower not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Unknown provider '{provider_name}'. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name_lower]
        return provider_class(**kwargs)

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """Retorna lista de proveedores disponibles"""
        return list(cls._providers.keys())


class ExchangeRateManager:
    """
    Manager central de tasas de cambio con fallback automático.

    Si un proveedor falla, intenta con el siguiente en la lista.
    """

    def __init__(self, provider_priority: list[str]):
        """
        Inicializa el manager con una lista de proveedores en orden de prioridad.

        Args:
            provider_priority: Lista de nombres de proveedores en orden
                              (ej: ['bcv', 'binance', 'mock'])
        """
        self.providers: list[ExchangeRateProvider] = []
        self.provider_names: list[str] = []

        for provider_name in provider_priority:
            try:
                provider = ExchangeRateProviderFactory.create(provider_name)
                self.providers.append(provider)
                self.provider_names.append(provider_name)
                logger.info(f"Added exchange rate provider: {provider_name}")
            except Exception as e:
                logger.error(f"Failed to create provider '{provider_name}': {e}")

        if not self.providers:
            raise RuntimeError("No exchange rate providers could be initialized")

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Obtiene tasa de cambio intentando con cada proveedor en orden.

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            date: Fecha opcional

        Returns:
            Decimal: Tasa de cambio o None si nadie la tiene
        """
        last_error = None

        for i, provider in enumerate(self.providers):
            try:
                logger.debug(f"Trying provider {self.provider_names[i]} for {from_currency}->{to_currency}")

                rate = provider.get_rate(from_currency, to_currency, date)

                if rate is not None:
                    logger.info(
                        f"Got rate {from_currency}->{to_currency}={rate} "
                        f"from {self.provider_names[i]}"
                    )
                    return rate

            except Exception as e:
                last_error = e
                logger.warning(
                    f"Provider {self.provider_names[i]} failed: {e}. "
                    f"Trying next provider..."
                )

        logger.error(f"All exchange rate providers failed for {from_currency}->{to_currency}")
        if last_error:
            raise ExchangeRateProviderError(
                f"All providers failed for {from_currency}->{to_currency}"
            ) from last_error

        return None

    def refresh_all(self) -> Dict[str, bool]:
        """
        Actualiza todos los proveedores.

        Returns:
            Dict con resultados por proveedor
        """
        results = {}

        for i, provider in enumerate(self.providers):
            try:
                results[self.provider_names[i]] = provider.refresh_rates()
            except Exception as e:
                logger.error(f"Failed to refresh {self.provider_names[i]}: {e}")
                results[self.provider_names[i]] = False

        return results

    def get_providers_status(self) -> Dict[str, bool]:
        """
        Retorna estado de disponibilidad de cada proveedor.

        Returns:
            Dict con estado por proveedor
        """
        status = {}

        for i, provider in enumerate(self.providers):
            try:
                status[self.provider_names[i]] = provider.is_available()
            except Exception as e:
                logger.error(f"Error checking {self.provider_names[i]} status: {e}")
                status[self.provider_names[i]] = False

        return status
