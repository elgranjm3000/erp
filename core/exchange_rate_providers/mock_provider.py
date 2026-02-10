"""
Mock Exchange Rate Provider
Útil para testing y desarrollo sin dependencias externas
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal

from .base import ExchangeRateProvider


logger = logging.getLogger(__name__)


class MockProvider(ExchangeRateProvider):
    """
    Proveedor mock de tasas de cambio para testing.

    Retorna tasas fijas predefinidas.
    """

    # Tasas mock (base: VES)
    MOCK_RATES = {
        "USD": Decimal("36.50"),
        "EUR": Decimal("39.80"),
        "CNY": Decimal("5.10"),
        "BRL": Decimal("7.30"),
        "USDT": Decimal("36.80"),  # Tether
    }

    SUPPORTED_CURRENCIES = list(MOCK_RATES.keys()) + ["VES"]

    _last_refresh: Optional[datetime] = None

    def __init__(self, custom_rates: Optional[dict] = None):
        """
        Inicializa proveedor mock.

        Args:
            custom_rates: Diccionario de tasas personalizadas
        """
        if custom_rates:
            self.MOCK_RATES.update(custom_rates)

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Obtiene tasa mock.

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            date: Ignorado (mock retorna siempre lo mismo)

        Returns:
            Decimal: Tasa de cambio
        """
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Caso 1: VES -> Otra moneda
        if from_currency == "VES" and to_currency in self.MOCK_RATES:
            return self.MOCK_RATES[to_currency]

        # Caso 2: Otra moneda -> VES (recíproco)
        if to_currency == "VES" and from_currency in self.MOCK_RATES:
            rate = self.MOCK_RATES[from_currency]
            if rate != 0:
                return Decimal("1") / rate

        # Caso 3: Entre monedas extranjeras
        if from_currency in self.MOCK_RATES and to_currency in self.MOCK_RATES:
            rate_from_ves = self.get_rate("VES", from_currency)
            rate_to_ves = self.get_rate(to_currency, "VES")
            if rate_from_ves and rate_to_ves:
                return rate_to_ves / rate_from_ves

        return None

    def get_supported_currencies(self) -> List[str]:
        """Retorna monedas soportadas"""
        return self.SUPPORTED_CURRENCIES.copy()

    def refresh_rates(self) -> bool:
        """Mock refresh (simula éxito)"""
        self._last_refresh = datetime.now()
        logger.info("Mock provider rates refreshed")
        return True

    def get_last_update_time(self) -> Optional[datetime]:
        return self._last_refresh

    def is_available(self) -> bool:
        """Mock siempre disponible"""
        return True
