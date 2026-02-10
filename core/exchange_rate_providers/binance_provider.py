"""
Binance Exchange Rate Provider
Obtiene tasas de cambio desde el mercado de criptomonedas
"""

import logging
from typing import Optional, List
from datetime import datetime, timedelta
from decimal import Decimal
import requests

from .base import ExchangeRateProvider, ProviderNotAvailableError


logger = logging.getLogger(__name__)


class BinanceProvider(ExchangeRateProvider):
    """
    Proveedor de tasas de cambio desde Binance.

    Útil para obtener tasa de USDT (Tether) en VES y otras criptos.
    """

    BINANCE_API_URL = "https://api.binance.com/api/v3"

    # Criptos soportadas
    SUPPORTED_CURRENCIES = ["USDT", "BTC", "ETH", "BNB"]

    # Par USDT-VES en Binance P2P
    USDT_VES_SYMBOL = "USDTVES"

    # Cache
    _rate_cache: dict = {}
    _last_refresh: Optional[datetime] = None
    _cache_ttl: timedelta = timedelta(minutes=5)  # 5 min para crypto

    def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        date: Optional[datetime] = None
    ) -> Optional[Decimal]:
        """
        Obtiene tasa de cambio desde Binance P2P.

        Args:
            from_currency: Moneda origen
            to_currency: Moneda destino
            date: Fecha (no soportado, solo tasa actual)

        Returns:
            Decimal: Tasa de cambio
        """
        if date:
            logger.warning("Binance provider does not support historical rates")
            return None

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        # Actualizar caché si es necesario
        if self._should_refresh_cache():
            try:
                self.refresh_rates()
            except Exception as e:
                logger.error(f"Failed to refresh Binance rates: {e}")
                if not self._rate_cache:
                    raise ProviderNotAvailableError(f"Binance unavailable: {e}")

        # Caso 1: USDT -> VES
        if from_currency == "USDT" and to_currency == "VES":
            return self._rate_cache.get("USDT_VES")

        # Caso 2: VES -> USDT (recíproco)
        if from_currency == "VES" and to_currency == "USDT":
            rate = self._rate_cache.get("USDT_VES")
            if rate and rate != 0:
                return Decimal("1") / rate

        return None

    def get_supported_currencies(self) -> List[str]:
        """Retorna monedas soportadas"""
        return ["USDT", "VES"]

    def refresh_rates(self) -> bool:
        """
        Actualiza tasa USDT/VES desde Binance P2P.

        Returns:
            bool: True si exitoso
        """
        try:
            # Obtener precio promedio de USDT en VES desde Binance P2P
            url = f"{self.BINANCE_API_URL}/ticker/price"
            params = {"symbol": "USDTVES"}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            rate = Decimal(str(data.get("price", "0")))

            if rate > 0:
                self._rate_cache["USDT_VES"] = rate
                self._last_refresh = datetime.now()
                logger.info(f"Binance USDT/VES rate: {rate}")
                return True
            else:
                logger.error("Invalid rate from Binance")
                return False

        except requests.RequestException as e:
            logger.error(f"HTTP error fetching Binance rates: {e}")
            raise ProviderNotAvailableError(f"Cannot connect to Binance: {e}")
        except Exception as e:
            logger.error(f"Error refreshing Binance rates: {e}")
            return False

    def get_last_update_time(self) -> Optional[datetime]:
        return self._last_refresh

    def is_available(self) -> bool:
        try:
            response = requests.get(f"{self.BINANCE_API_URL}/ping", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def _should_refresh_cache(self) -> bool:
        if not self._last_refresh:
            return True
        return datetime.now() - self._last_refresh > self._cache_ttl
