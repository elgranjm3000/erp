"""
Exchange Rate Providers Package
Patrón Provider para obtener tasas de cambio de múltiples fuentes
"""

from .base import (
    ExchangeRateProvider,
    ExchangeRateProviderError,
    ProviderNotAvailableError,
    CurrencyNotSupportedError
)

from .bcv_provider import BCVProvider
from .binance_provider import BinanceProvider
from .mock_provider import MockProvider
from .factory import (
    ExchangeRateProviderFactory,
    ExchangeRateManager
)

__all__ = [
    # Base
    "ExchangeRateProvider",
    "ExchangeRateProviderError",
    "ProviderNotAvailableError",
    "CurrencyNotSupportedError",

    # Providers
    "BCVProvider",
    "BinanceProvider",
    "MockProvider",

    # Factory
    "ExchangeRateProviderFactory",
    "ExchangeRateManager",
]
