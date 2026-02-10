"""
Abstract Base Provider for Exchange Rates
Implementa el patrón Provider para tasas de cambio
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, List
from datetime import datetime
from decimal import Decimal


class ExchangeRateProvider(ABC):
    """
    Interfaz abstracta para proveedores de tasas de cambio.

    Cada proveedor (BCV, Binance, Fixer, etc.) debe implementar
    estos métodos para obtener tasas de cambio de forma estandarizada.
    """

    @abstractmethod
    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Obtiene la tasa de cambio entre dos monedas.

        Args:
            from_currency: Código de moneda origen (ej: 'USD', 'EUR')
            to_currency: Código de moneda destino (ej: 'VES', 'USD')
            date: Fecha opcional para tasa histórica

        Returns:
            Decimal: Tasa de cambio o None si no está disponible
        """
        pass

    @abstractmethod
    def get_supported_currencies(self) -> List[str]:
        """
        Retorna la lista de códigos de moneda soportados.

        Returns:
            List[str]: Lista de códigos (ej: ['USD', 'EUR', 'VES'])
        """
        pass

    @abstractmethod
    def refresh_rates(self) -> bool:
        """
        Fuerza la actualización de tasas desde la fuente.

        Returns:
            bool: True si la actualización fue exitosa
        """
        pass

    @abstractmethod
    def get_last_update_time(self) -> Optional[datetime]:
        """
        Retorna la timestamp de la última actualización exitosa.

        Returns:
            datetime: Timestamp de última actualización
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Verifica si el proveedor está disponible y funcionando.

        Returns:
            bool: True si el proveedor está disponible
        """
        pass


class ExchangeRateProviderError(Exception):
    """Excepción base para errores de proveedores de tasas"""
    pass


class ProviderNotAvailableError(ExchangeRateProviderError):
    """Error cuando el proveedor no está disponible"""
    pass


class CurrencyNotSupportedError(ExchangeRateProviderError):
    """Error cuando una moneda no está soportada"""
    pass
